import os, sqlite3, secrets, datetime as dt
from functools import wraps
from flask import Flask, g, render_template, request, redirect, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
DB = os.environ.get("DB_PATH") or ("/tmp/helpdesk.db" if os.environ.get("VERCEL") else "helpdesk.db")
SLA = {"Critical": (15, 240), "High": (30, 480), "Medium": (240, 1440), "Low": (480, 2880)}  # minutes
STATUSES = ["Open", "Assigned", "In Progress", "Pending User", "Pending Third Party", "Resolved", "Closed", "Reopened"]
DONE = "status not in ('Resolved','Closed')"
TQ = ("select t.*,c.name cat,u.full_name requester,a.full_name tech from tickets t "
      "join categories c on c.id=t.category_id join users u on u.id=t.created_by "
      "left join users a on a.id=t.assigned_to ")

SCHEMA = """
create table if not exists users(id integer primary key,full_name text,email text unique,password_hash text,role text,department text,is_active int default 1,created_at text);
create table if not exists categories(id integer primary key,name text,is_active int default 1);
create table if not exists tickets(id integer primary key,ticket_number text unique,request_type text,subject text,description text,
 category_id int references categories(id),created_by int references users(id),assigned_to int references users(id),priority text,status text,
 affected_device text,created_at text,updated_at text,response_due text,resolve_due text,first_response_at text,resolved_at text,closed_at text,resolution text);
create table if not exists comments(id integer primary key,ticket_id int references tickets(id),user_id int references users(id),body text,created_at text);
create table if not exists work_logs(id integer primary key,ticket_id int references tickets(id),technician_id int references users(id),activity text,minutes int,created_at text);
create table if not exists knowledge_articles(id integer primary key,title text,category_id int,symptoms text,diagnostics text,resolution text,created_at text);
create table if not exists audit_logs(id integer primary key,user_id int,ticket_id int,action text,old_value text,new_value text,created_at text);
create index if not exists ix_t_status on tickets(status,priority,assigned_to);
"""

def now(): return dt.datetime.utcnow().replace(microsecond=0)
def iso(d): return d.isoformat(sep=" ")
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB); g.db.row_factory = sqlite3.Row
        g.db.execute("pragma foreign_keys=on")
    return g.db
@app.teardown_appcontext
def _close(e):
    d = g.pop("db", None)
    if d: d.close()
def q(sql, *a, one=False):
    r = db().execute(sql, a).fetchall()
    return (r[0] if r else None) if one else r
def run(sql, *a):
    c = db().execute(sql, a); db().commit(); return c.lastrowid
def audit(uid, tid, action, old=None, new=None):
    run("insert into audit_logs(user_id,ticket_id,action,old_value,new_value,created_at) values(?,?,?,?,?,?)", uid, tid, action, old, new, iso(now()))

def prio(impact, urgency):
    s = impact + urgency
    return "Critical" if s >= 6 else "High" if s == 5 else "Medium" if s == 4 else "Low"

def create_ticket(kind, subject, desc, cat, imp, urg, uid, device="", tech=None, status="Open", created=None, resolved_h=None, resolution=None):
    pr = prio(imp, urg); c = created or now(); rm, sm = SLA[pr]
    num = f"{kind}-{q('select count(*) c from tickets where request_type=?', kind, one=True)['c'] + 1001}"
    fr = iso(c + dt.timedelta(minutes=12)) if tech else None
    rs = iso(c + dt.timedelta(hours=resolved_h)) if resolved_h else None
    tid = run("insert into tickets(ticket_number,request_type,subject,description,category_id,created_by,assigned_to,priority,status,affected_device,created_at,updated_at,response_due,resolve_due,first_response_at,resolved_at,resolution) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              num, kind, subject, desc, cat, uid, tech, pr, status, device, iso(c), iso(c), iso(c + dt.timedelta(minutes=rm)), iso(c + dt.timedelta(minutes=sm)), fr, rs, resolution)
    audit(uid, tid, "created", None, num)
    return tid

def sla(t):
    n, out = iso(now()), {}
    for k, due, done in (("Response", "response_due", "first_response_at"), ("Resolution", "resolve_due", "resolved_at")):
        out[k] = ("Met" if t[done] <= t[due] else "Breached") if t[done] else ("Breached" if n > t[due] else "Running")
    return out

def init():
    db().executescript(SCHEMA)
    if q("select count(*) c from users", one=True)["c"]: return
    h, t = generate_password_hash("Password123!"), iso(now())
    for n, e, r, d in [("Priya Nair", "employee@company.com", "employee", "Finance"), ("Arjun Mehta", "technician@company.com", "technician", "IT"),
                       ("Sana Khan", "technician2@company.com", "technician", "IT"), ("Rahul Verma", "admin@company.com", "administrator", "IT")]:
        run("insert into users(full_name,email,password_hash,role,department,created_at) values(?,?,?,?,?,?)", n, e, h, r, d, t)
    db().execute("update users set role='admin' where role='administrator'"); db().commit()
    for c in ["Hardware", "Software", "Network", "Account & Access", "Email", "Printer & Peripherals"]:
        run("insert into categories(name) values(?)", c)
    H = lambda x: dt.timedelta(hours=x)
    for k, s, c, i, u, st, ago, tech, rh, res in [
        ("INC", "Wi-Fi connected but no websites load", 3, 3, 3, "Resolved", 30, 2, 2.5, "Incorrect DNS server on adapter; reset to DHCP and verified with nslookup."),
        ("INC", "Outlook not receiving new emails", 5, 2, 3, "In Progress", 3, 2, None, None),
        ("INC", "Printer offline on 2nd floor", 6, 2, 2, "Pending User", 20, 3, None, None),
        ("SR", "Access to shared Finance folder", 4, 1, 2, "Assigned", 5, 3, None, None),
        ("INC", "VPN disconnects every 10 minutes", 3, 3, 2, "Resolved", 60, 3, 9, "Updated VPN client; stable for 24h."),
        ("INC", "Laptop running very slowly", 1, 2, 2, "Open", 1, None, None, None),
        ("SR", "Install Adobe Acrobat", 2, 1, 1, "Closed", 90, 2, 6, "Installed and confirmed by user.")]:
        create_ticket(k, s, "Reported by user via portal. " + s + ".", c, i, u, 1, "Dell Latitude 5440", tech, st, now() - H(ago), rh, res)
    for ti, c, sy, di, re in [
        ("Troubleshoot internet connectivity", 3, "Browser cannot load sites; Wi-Fi shows connected.", "ipconfig /all; ping gateway; ping 8.8.8.8; nslookup google.com", "Fix DNS or DHCP lease (ipconfig /release, /renew, /flushdns). Verify browsing."),
        ("Investigate high CPU utilization", 1, "Fans loud, system slow.", "Task Manager > Processes; Get-Process | sort CPU -desc | select -first 5", "End or update offending process; review startup apps. Escalate if kernel/driver related."),
        ("Resolve Outlook not receiving email", 5, "Inbox not updating; Send/Receive errors.", "Check Work Offline, mailbox quota, profile health, Event Viewer", "Rebuild Outlook profile or clear quota. Verify test email arrives.")]:
        run("insert into knowledge_articles(title,category_id,symptoms,diagnostics,resolution,created_at) values(?,?,?,?,?,?)", ti, c, sy, di, re, t)

with app.app_context(): init()

@app.before_request
def _load():
    g.user = q("select * from users where id=? and is_active=1", session["uid"], one=True) if "uid" in session else None
    if request.method == "POST" and not secrets.compare_digest(request.form.get("csrf", ""), session.get("csrf", "x")): abort(400)
@app.context_processor
def _ctx():
    session.setdefault("csrf", secrets.token_hex(16))
    return dict(user=g.get("user"), csrf=session["csrf"], sla=sla)

def need(*roles):
    def deco(f):
        @wraps(f)
        def w(*a, **k):
            if not g.user: return redirect("/login")
            if roles and g.user["role"] not in roles: abort(403)
            return f(*a, **k)
        return w
    return deco

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = q("select * from users where email=? and is_active=1", request.form.get("email", "").strip().lower(), one=True)
        if u and check_password_hash(u["password_hash"], request.form.get("password", "")):
            session.clear(); session["uid"] = u["id"]; session["csrf"] = secrets.token_hex(16)
            return redirect("/")
        flash("Email or password is incorrect.")
    return render_template("login.html")

@app.post("/logout")
def logout():
    session.clear(); return redirect("/login")

@app.route("/")
@need()
def home():
    if g.user["role"] == "employee":
        return render_template("dashboard.html", stats=None, rows=q(TQ + "where t.created_by=? order by t.id desc limit 8", g.user["id"]))
    n = iso(now()); one = lambda s, *a: q(s, *a, one=True)[0]
    res = q("select resolved_at<=resolve_due ok,(julianday(resolved_at)-julianday(created_at))*24 h from tickets where resolved_at is not null")
    s = dict(total=one("select count(*) from tickets"), open=one(f"select count(*) from tickets where {DONE}"),
             overdue=one(f"select count(*) from tickets where {DONE} and resolve_due<?", n),
             comp=round(100 * sum(r["ok"] for r in res) / len(res)) if res else None,
             avg=round(sum(r["h"] for r in res) / len(res), 1) if res else None,
             status=[(x, one("select count(*) from tickets where status=?", x)) for x in STATUSES],
             prio=[(x, one("select count(*) from tickets where priority=?", x)) for x in SLA],
             cat=q("select c.name,count(*) n from tickets t join categories c on c.id=t.category_id group by c.name order by n desc"),
             load=q(f"select u.full_name,count(t.id) n from users u left join tickets t on t.assigned_to=u.id and t.{DONE} where u.role='technician' group by u.id"))
    return render_template("dashboard.html", stats=s, rows=q(TQ + "order by t.id desc limit 6"))

@app.route("/tickets")
@need()
def tickets():
    st, term, sql, a = request.args.get("status", ""), request.args.get("q", "").strip(), TQ + "where 1=1", []
    if g.user["role"] == "employee": sql += " and t.created_by=?"; a.append(g.user["id"])
    if st in STATUSES: sql += " and t.status=?"; a.append(st)
    if term: sql += " and (t.subject like ? or t.ticket_number like ?)"; a += [f"%{term}%"] * 2
    return render_template("tickets.html", rows=q(sql + " order by t.id desc", *a), st=st, term=term, statuses=STATUSES)

def num(v):
    try: return min(max(int(v), 1), 3)
    except (TypeError, ValueError): return 1

@app.route("/tickets/new", methods=["GET", "POST"])
@need()
def new():
    cats = q("select * from categories where is_active=1")
    if request.method == "POST":
        f = request.form; sub, desc = f.get("subject", "").strip()[:150], f.get("description", "").strip()[:4000]
        cat = q("select id from categories where id=?", f.get("category"), one=True)
        if not (sub and desc and cat):
            flash("Subject, category and description are required."); return render_template("new.html", cats=cats)
        tid = create_ticket("SR" if f.get("kind") == "SR" else "INC", sub, desc, cat["id"], num(f.get("impact")), num(f.get("urgency")), g.user["id"], f.get("device", "")[:80])
        return redirect(f"/tickets/{tid}")
    return render_template("new.html", cats=cats)

def get_ticket(tid):
    t = q(TQ + "where t.id=?", tid, one=True)
    if not t: abort(404)
    if g.user["role"] == "employee" and t["created_by"] != g.user["id"]: abort(403)
    return t

@app.get("/tickets/<int:tid>")
@need()
def ticket(tid):
    t = get_ticket(tid)
    ev = [("comment", r["full_name"], r["body"], r["created_at"]) for r in q("select c.*,u.full_name from comments c join users u on u.id=c.user_id where ticket_id=?", tid)]
    if g.user["role"] != "employee":
        ev += [("worklog", r["full_name"], f"{r['activity']} ({r['minutes']} min)", r["created_at"]) for r in q("select w.*,u.full_name from work_logs w join users u on u.id=w.technician_id where ticket_id=?", tid)]
    return render_template("ticket.html", t=t, ev=sorted(ev, key=lambda e: e[3]), techs=q("select id,full_name from users where role='technician' and is_active=1"))

@app.post("/tickets/<int:tid>/<act>")
@need()
def act(tid, act):
    t, u, f, n = get_ticket(tid), g.user, request.form, iso(now()); staff = u["role"] != "employee"
    first = ",first_response_at=coalesce(first_response_at,?)" if staff else ""
    if act == "comment" and f.get("body", "").strip():
        run("insert into comments(ticket_id,user_id,body,created_at) values(?,?,?,?)", tid, u["id"], f["body"].strip()[:2000], n)
        if staff: run("update tickets set first_response_at=coalesce(first_response_at,?) where id=?", n, tid)
        audit(u["id"], tid, "comment")
    elif act == "worklog" and staff and f.get("activity", "").strip():
        run("insert into work_logs(ticket_id,technician_id,activity,minutes,created_at) values(?,?,?,?,?)", tid, u["id"], f["activity"].strip()[:2000], max(0, min(int(f.get("minutes") or 0), 1440)) if (f.get("minutes") or "0").isdigit() else 0, n)
        run("update tickets set first_response_at=coalesce(first_response_at,?) where id=?", n, tid); audit(u["id"], tid, "work log")
    elif act == "assign" and u["role"] == "admin":
        tech = q("select id,full_name from users where id=? and role='technician' and is_active=1", f.get("tech"), one=True)
        if tech:
            run("update tickets set assigned_to=?,status=case when status='Open' then 'Assigned' else status end,updated_at=? where id=?", tech["id"], n, tid)
            audit(u["id"], tid, "assigned", t["tech"], tech["full_name"])
    elif act == "status":
        new, cur, res = f.get("status", ""), t["status"], f.get("resolution", "").strip()[:2000]
        ok = (staff and new in ("In Progress", "Pending User", "Pending Third Party", "Resolved", "Reopened")) or (u["role"] == "admin" and new == "Closed") \
            or (not staff and ((new == "Closed" and cur == "Resolved") or (new == "Reopened" and cur in ("Resolved", "Closed"))))
        if cur == "Closed" and new != "Reopened": ok = False
        if not ok: flash("That status change is not allowed.")
        elif new in ("Resolved", "Closed") and not (res or t["resolution"]): flash("Add resolution details before resolving or closing.")
        else:
            sets, args = "status=?,updated_at=?", [new, n]
            if res: sets += ",resolution=?"; args.append(res)
            if new == "Resolved" or (new == "Closed" and not t["resolved_at"]): sets += ",resolved_at=?"; args.append(n)
            if new == "Closed": sets += ",closed_at=?"; args.append(n)
            if new == "Reopened": sets += ",resolved_at=null,closed_at=null"
            if staff: sets += first; args.append(n)
            run(f"update tickets set {sets} where id=?", *args, tid); audit(u["id"], tid, "status", cur, new)
    return redirect(f"/tickets/{tid}")

@app.route("/kb")
@need()
def kb():
    term = request.args.get("q", "").strip()
    rows = q("select k.*,c.name cat from knowledge_articles k join categories c on c.id=k.category_id where k.title like ? or k.symptoms like ?", f"%{term}%", f"%{term}%")
    return render_template("kb.html", rows=rows, term=term)

@app.route("/audit")
@need("admin")
def audit_log():
    return render_template("audit.html", rows=q("select a.*,u.full_name,t.ticket_number from audit_logs a left join users u on u.id=a.user_id left join tickets t on t.id=a.ticket_id order by a.id desc limit 200"))

if __name__ == "__main__":
    app.run(debug=False)
