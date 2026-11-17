from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.ticket import Ticket, Category, Comment, AuditLog
from datetime import datetime

employee_bp = Blueprint('employee', __name__)

def employee_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('employee', 'admin'):
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@employee_bp.route('/dashboard')
@login_required
@employee_required
def dashboard():
    tickets = Ticket.query.filter_by(created_by=current_user.id).order_by(Ticket.created_at.desc()).all()
    open_count = sum(1 for t in tickets if t.status not in ('Resolved', 'Closed'))
    return render_template('employee/dashboard.html', tickets=tickets, open_count=open_count)

@employee_bp.route('/tickets/new', methods=['GET', 'POST'])
@login_required
@employee_required
def create_ticket():
    categories = Category.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        request_type = request.form.get('request_type', 'Incident')
        subject = request.form.get('subject', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id')
        priority = request.form.get('priority', 'Medium')
        affected_device = request.form.get('affected_device', '')
        location = request.form.get('location', '')
        impact = request.form.get('impact', 'Medium')
        urgency = request.form.get('urgency', 'Medium')
        
        if not subject or not description:
            flash('Subject and description are required.', 'danger')
            return render_template('employee/create_ticket.html', categories=categories)
        
        # Generate ticket number
        prefix = 'INC' if request_type == 'Incident' else 'SR'
        last = Ticket.query.filter(Ticket.ticket_number.like(f'{prefix}-%')).order_by(Ticket.id.desc()).first()
        if last:
            try:
                num = int(last.ticket_number.split('-')[1]) + 1
            except:
                num = 1001
        else:
            num = 1001
        ticket_number = f'{prefix}-{num}'
        
        # Simple priority matrix
        if impact == 'High' and urgency == 'High':
            priority = 'Critical'
        elif impact == 'High' or urgency == 'High':
            priority = 'High'
        elif impact == 'Low' and urgency == 'Low':
            priority = 'Low'
        else:
            priority = 'Medium'
        
        ticket = Ticket(
            ticket_number=ticket_number,
            request_type=request_type,
            subject=subject,
            description=description,
            category_id=int(category_id) if category_id else None,
            created_by=current_user.id,
            priority=priority,
            status='Open',
            affected_device=affected_device,
            location=location,
            impact=impact,
            urgency=urgency
        )
        db.session.add(ticket)
        db.session.flush()
        
        audit = AuditLog(user_id=current_user.id, ticket_id=ticket.id, action='Ticket created', new_value=ticket_number)
        db.session.add(audit)
        db.session.commit()
        
        flash(f'Ticket {ticket_number} created successfully.', 'success')
        return redirect(url_for('employee.view_ticket', ticket_id=ticket.id))
    
    return render_template('employee/create_ticket.html', categories=categories)

@employee_bp.route('/tickets/<int:ticket_id>')
@login_required
@employee_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.created_by != current_user.id and current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('employee.dashboard'))
    comments = ticket.comments.order_by(Comment.created_at.asc()).all()
    work_logs = ticket.work_logs.order_by(WorkLog.created_at.asc()).all() if hasattr(ticket, 'work_logs') else []
    from app.models.ticket import WorkLog
    work_logs = WorkLog.query.filter_by(ticket_id=ticket.id).order_by(WorkLog.created_at.asc()).all()
    sla = ticket.calculate_sla_status()
    return render_template('employee/view_ticket.html', ticket=ticket, comments=comments, work_logs=work_logs, sla=sla)

@employee_bp.route('/tickets/<int:ticket_id>/comment', methods=['POST'])
@login_required
@employee_required
def add_comment(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.created_by != current_user.id and current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('employee.dashboard'))
    comment_text = request.form.get('comment', '').strip()
    if comment_text:
        c = Comment(ticket_id=ticket.id, user_id=current_user.id, comment=comment_text)
        db.session.add(c)
        audit = AuditLog(user_id=current_user.id, ticket_id=ticket.id, action='Comment added')
        db.session.add(audit)
        db.session.commit()
        flash('Comment added.', 'success')
    return redirect(url_for('employee.view_ticket', ticket_id=ticket.id))

@employee_bp.route('/tickets/<int:ticket_id>/confirm', methods=['POST'])
@login_required
@employee_required
def confirm_resolution(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.created_by != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('employee.dashboard'))
    if ticket.status == 'Resolved':
        ticket.status = 'Closed'
        ticket.closed_at = datetime.utcnow()
        audit = AuditLog(user_id=current_user.id, ticket_id=ticket.id, action='Ticket closed by user confirmation')
        db.session.add(audit)
        db.session.commit()
        flash('Ticket closed. Thank you for confirming.', 'success')
    return redirect(url_for('employee.view_ticket', ticket_id=ticket.id))
