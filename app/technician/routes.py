from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.ticket import Ticket, Comment, WorkLog, Assignment, AuditLog, KnowledgeArticle
from datetime import datetime
from functools import wraps

technician_bp = Blueprint('technician', __name__)

def tech_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('technician', 'admin'):
            flash('Access denied. Technicians only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@technician_bp.route('/dashboard')
@login_required
@tech_required
def dashboard():
    assigned = Ticket.query.filter_by(assigned_to=current_user.id).filter(Ticket.status.notin_(['Closed'])).order_by(Ticket.created_at.desc()).all()
    unassigned = Ticket.query.filter_by(assigned_to=None).filter(Ticket.status == 'Open').order_by(Ticket.created_at.desc()).all()
    high_priority = Ticket.query.filter(Ticket.priority.in_(['Critical', 'High']), Ticket.status.notin_(['Resolved', 'Closed'])).order_by(Ticket.created_at.desc()).limit(10).all()
    
    my_open = sum(1 for t in assigned if t.status not in ('Resolved', 'Closed'))
    return render_template('technician/dashboard.html', 
                           assigned=assigned, unassigned=unassigned, high_priority=high_priority, my_open=my_open)

@technician_bp.route('/tickets/<int:ticket_id>')
@login_required
@tech_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    comments = Comment.query.filter_by(ticket_id=ticket.id).order_by(Comment.created_at.asc()).all()
    work_logs = WorkLog.query.filter_by(ticket_id=ticket.id).order_by(WorkLog.created_at.asc()).all()
    sla = ticket.calculate_sla_status()
    techs = User.query.filter(User.role.in_(['technician', 'admin']), User.is_active==True).all()
    return render_template('technician/view_ticket.html', ticket=ticket, comments=comments, work_logs=work_logs, sla=sla, techs=techs)

@technician_bp.route('/tickets/<int:ticket_id>/accept', methods=['POST'])
@login_required
@tech_required
def accept_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.assigned_to and ticket.assigned_to != current_user.id:
        flash('Ticket already assigned to another technician.', 'warning')
        return redirect(url_for('technician.view_ticket', ticket_id=ticket.id))
    
    ticket.assigned_to = current_user.id
    ticket.status = 'Assigned'
    if not ticket.first_response_at:
        ticket.first_response_at = datetime.utcnow()
    
    assign = Assignment(ticket_id=ticket.id, assigned_by=current_user.id, assigned_to=current_user.id)
    db.session.add(assign)
    audit = AuditLog(user_id=current_user.id, ticket_id=ticket.id, action='Ticket accepted/assigned', new_value=current_user.full_name)
    db.session.add(audit)
    db.session.commit()
    flash('Ticket accepted.', 'success')
    return redirect(url_for('technician.view_ticket', ticket_id=ticket.id))

@technician_bp.route('/tickets/<int:ticket_id>/status', methods=['POST'])
@login_required
@tech_required
def update_status(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    new_status = request.form.get('status')
    allowed = ['Assigned', 'In Progress', 'Pending User', 'Pending Third Party', 'Resolved', 'Closed', 'Reopened']
    if new_status not in allowed:
        flash('Invalid status.', 'danger')
        return redirect(url_for('technician.view_ticket', ticket_id=ticket.id))
    
    old = ticket.status
    ticket.status = new_status
    ticket.updated_at = datetime.utcnow()
    
    if new_status == 'In Progress' and not ticket.first_response_at:
        ticket.first_response_at = datetime.utcnow()
    if new_status == 'Resolved':
        ticket.resolved_at = datetime.utcnow()
        ticket.resolution_notes = request.form.get('resolution_notes', '')
    if new_status == 'Closed':
        ticket.closed_at = datetime.utcnow()
    
    audit = AuditLog(user_id=current_user.id, ticket_id=ticket.id, action='Status changed', old_value=old, new_value=new_status)
    db.session.add(audit)
    db.session.commit()
    flash(f'Status updated to {new_status}.', 'success')
    return redirect(url_for('technician.view_ticket', ticket_id=ticket.id))

@technician_bp.route('/tickets/<int:ticket_id>/worklog', methods=['POST'])
@login_required
@tech_required
def add_worklog(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    desc = request.form.get('activity_description', '').strip()
    time_spent = request.form.get('time_spent', 0)
    try:
        time_spent = int(time_spent)
    except:
        time_spent = 0
    
    if desc:
        wl = WorkLog(ticket_id=ticket.id, technician_id=current_user.id, activity_description=desc, time_spent_minutes=time_spent)
        db.session.add(wl)
        if not ticket.first_response_at:
            ticket.first_response_at = datetime.utcnow()
            ticket.status = 'In Progress'
        audit = AuditLog(user_id=current_user.id, ticket_id=ticket.id, action='Work log added')
        db.session.add(audit)
        db.session.commit()
        flash('Work log added.', 'success')
    return redirect(url_for('technician.view_ticket', ticket_id=ticket.id))

@technician_bp.route('/tickets/<int:ticket_id>/comment', methods=['POST'])
@login_required
@tech_required
def add_comment(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    comment_text = request.form.get('comment', '').strip()
    is_internal = request.form.get('is_internal') == 'on'
    if comment_text:
        c = Comment(ticket_id=ticket.id, user_id=current_user.id, comment=comment_text, is_internal=is_internal)
        db.session.add(c)
        if not ticket.first_response_at:
            ticket.first_response_at = datetime.utcnow()
        audit = AuditLog(user_id=current_user.id, ticket_id=ticket.id, action='Comment added')
        db.session.add(audit)
        db.session.commit()
        flash('Comment added.', 'success')
    return redirect(url_for('technician.view_ticket', ticket_id=ticket.id))

@technician_bp.route('/tickets/<int:ticket_id>/assign', methods=['POST'])
@login_required
@tech_required
def reassign(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    tech_id = request.form.get('technician_id')
    reason = request.form.get('reason', '')
    if tech_id:
        old = ticket.assigned_to
        ticket.assigned_to = int(tech_id)
        ticket.status = 'Assigned'
        assign = Assignment(ticket_id=ticket.id, assigned_by=current_user.id, assigned_to=int(tech_id), reassignment_reason=reason)
        db.session.add(assign)
        audit = AuditLog(user_id=current_user.id, ticket_id=ticket.id, action='Ticket reassigned', old_value=str(old), new_value=tech_id)
        db.session.add(audit)
        db.session.commit()
        flash('Ticket reassigned.', 'success')
    return redirect(url_for('technician.view_ticket', ticket_id=ticket.id))

@technician_bp.route('/knowledge')
@login_required
@tech_required
def knowledge_base():
    articles = KnowledgeArticle.query.filter_by(is_published=True).order_by(KnowledgeArticle.title).all()
    return render_template('technician/knowledge.html', articles=articles)

@technician_bp.route('/knowledge/<int:article_id>')
@login_required
@tech_required
def view_article(article_id):
    article = KnowledgeArticle.query.get_or_404(article_id)
    return render_template('technician/view_article.html', article=article)
