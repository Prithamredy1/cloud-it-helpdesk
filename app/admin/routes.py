from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.ticket import Ticket, Category, SLAPolicy, KnowledgeArticle, AuditLog, Assignment
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total = Ticket.query.count()
    open_t = Ticket.query.filter(Ticket.status.notin_(['Resolved', 'Closed'])).count()
    resolved = Ticket.query.filter_by(status='Resolved').count()
    closed = Ticket.query.filter_by(status='Closed').count()
    overdue = 0
    for t in Ticket.query.filter(Ticket.status.notin_(['Resolved', 'Closed'])).all():
        sla = t.calculate_sla_status()
        if sla.get('resolution_overdue'):
            overdue += 1
    
    by_priority = db.session.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()
    by_status = db.session.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
    by_category = db.session.query(Category.category_name, func.count(Ticket.id)).join(Ticket, Ticket.category_id==Category.id).group_by(Category.category_name).all()
    
    # Workload
    techs = User.query.filter(User.role.in_(['technician', 'admin']), User.is_active==True).all()
    workload = []
    for tech in techs:
        count = Ticket.query.filter_by(assigned_to=tech.id).filter(Ticket.status.notin_(['Resolved', 'Closed'])).count()
        workload.append({'name': tech.full_name, 'count': count})
    
    # Recent tickets
    recent = Ticket.query.order_by(Ticket.created_at.desc()).limit(10).all()
    
    # SLA compliance (simple)
    resolved_tickets = Ticket.query.filter(Ticket.resolved_at.isnot(None)).all()
    met = 0
    for t in resolved_tickets:
        sla = t.calculate_sla_status()
        if sla.get('resolution_met'):
            met += 1
    compliance = round((met / len(resolved_tickets) * 100) if resolved_tickets else 100, 1)
    
    return render_template('admin/dashboard.html',
                           total=total, open_t=open_t, resolved=resolved, closed=closed, overdue=overdue,
                           by_priority=by_priority, by_status=by_status, by_category=by_category,
                           workload=workload, recent=recent, compliance=compliance)

@admin_bp.route('/tickets')
@login_required
@admin_required
def all_tickets():
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    q = Ticket.query
    if status:
        q = q.filter_by(status=status)
    if priority:
        q = q.filter_by(priority=priority)
    tickets = q.order_by(Ticket.created_at.desc()).all()
    return render_template('admin/tickets.html', tickets=tickets)

@admin_bp.route('/tickets/<int:ticket_id>')
@login_required
@admin_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    from app.models.ticket import Comment, WorkLog
    comments = Comment.query.filter_by(ticket_id=ticket.id).order_by(Comment.created_at.asc()).all()
    work_logs = WorkLog.query.filter_by(ticket_id=ticket.id).order_by(WorkLog.created_at.asc()).all()
    sla = ticket.calculate_sla_status()
    techs = User.query.filter(User.role.in_(['technician', 'admin']), User.is_active==True).all()
    return render_template('admin/view_ticket.html', ticket=ticket, comments=comments, work_logs=work_logs, sla=sla, techs=techs)

@admin_bp.route('/tickets/<int:ticket_id>/assign', methods=['POST'])
@login_required
@admin_required
def assign_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    tech_id = request.form.get('technician_id')
    if tech_id:
        ticket.assigned_to = int(tech_id)
        ticket.status = 'Assigned'
        assign = Assignment(ticket_id=ticket.id, assigned_by=current_user.id, assigned_to=int(tech_id))
        db.session.add(assign)
        audit = AuditLog(user_id=current_user.id, ticket_id=ticket.id, action='Ticket assigned by admin', new_value=tech_id)
        db.session.add(audit)
        db.session.commit()
        flash('Ticket assigned.', 'success')
    return redirect(url_for('admin.view_ticket', ticket_id=ticket.id))

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.order_by(User.role, User.full_name).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', 'employee')
        department = request.form.get('department', '')
        password = request.form.get('password', 'ChangeMe@123')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
        else:
            user = User(full_name=full_name, email=email, role=role, department=department)
            user.set_password(password)
            db.session.add(user)
            audit = AuditLog(user_id=current_user.id, action=f'User created: {email}')
            db.session.add(audit)
            db.session.commit()
            flash(f'User {email} created.', 'success')
            return redirect(url_for('admin.users'))
    return render_template('admin/create_user.html')

@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot deactivate yourself.', 'warning')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash(f'User {"activated" if user.is_active else "deactivated"}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    cats = Category.query.all()
    return render_template('admin/categories.html', categories=cats)

@admin_bp.route('/sla')
@login_required
@admin_required
def sla_policies():
    policies = SLAPolicy.query.all()
    return render_template('admin/sla.html', policies=policies)

@admin_bp.route('/audit')
@login_required
@admin_required
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return render_template('admin/audit.html', logs=logs)

@admin_bp.route('/knowledge')
@login_required
@admin_required
def knowledge():
    articles = KnowledgeArticle.query.order_by(KnowledgeArticle.created_at.desc()).all()
    return render_template('admin/knowledge.html', articles=articles)
