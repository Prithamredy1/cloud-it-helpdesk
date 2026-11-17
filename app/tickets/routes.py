from flask import Blueprint, redirect, url_for
from flask_login import login_required, current_user

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route('/<int:ticket_id>')
@login_required
def view(ticket_id):
    if current_user.role == 'admin':
        return redirect(url_for('admin.view_ticket', ticket_id=ticket_id))
    elif current_user.role == 'technician':
        return redirect(url_for('technician.view_ticket', ticket_id=ticket_id))
    else:
        return redirect(url_for('employee.view_ticket', ticket_id=ticket_id))
