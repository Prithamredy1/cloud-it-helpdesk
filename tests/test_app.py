import os, tempfile
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "t.db")
import app as A

def login(c, email):
    c.get("/login")
    with c.session_transaction() as s: tok = s["csrf"]
    return c.post("/login", data={"email": email, "password": "Password123!", "csrf": tok})

def tok(c):
    with c.session_transaction() as s: return s["csrf"]

def test_priority_matrix():
    assert A.prio(3, 3) == "Critical" and A.prio(3, 2) == "High" and A.prio(2, 2) == "Medium" and A.prio(1, 1) == "Low"

def test_anonymous_redirected():
    assert A.app.test_client().get("/").status_code == 302

def test_bad_password():
    c = A.app.test_client(); c.get("/login")
    r = c.post("/login", data={"email": "admin@company.com", "password": "x", "csrf": tok(c)})
    assert b"incorrect" in r.data

def test_rbac():
    c = A.app.test_client(); login(c, "employee@company.com")
    assert c.get("/").status_code == 200 and c.get("/audit").status_code == 403
    a = A.app.test_client(); login(a, "admin@company.com")
    assert a.get("/audit").status_code == 200

def test_csrf_blocks_post():
    c = A.app.test_client(); login(c, "employee@company.com")
    assert c.post("/tickets/new", data={"subject": "x"}).status_code == 400

def test_create_ticket_and_resolution_rule():
    c = A.app.test_client(); login(c, "employee@company.com")
    r = c.post("/tickets/new", data={"subject": "Mouse dead", "description": "No cursor", "category": "1", "impact": "1", "urgency": "1", "csrf": tok(c)})
    assert r.status_code == 302
    t = r.headers["Location"]
    tc = A.app.test_client(); login(tc, "technician@company.com")
    tc.post(t + "/status", data={"status": "Resolved", "csrf": tok(tc)})
    assert b"Resolved</span>" not in tc.get(t).data  # blocked: no resolution text
    tc.post(t + "/status", data={"status": "Resolved", "resolution": "Replaced mouse", "csrf": tok(tc)})
    assert b"Replaced mouse" in tc.get(t).data
