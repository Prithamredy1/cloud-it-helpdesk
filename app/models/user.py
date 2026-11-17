from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')  # employee, technician, admin
    department = db.Column(db.String(80))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tickets_created = db.relationship('Ticket', backref='creator', lazy='dynamic', foreign_keys='Ticket.created_by')
    tickets_assigned = db.relationship('Ticket', backref='assignee', lazy='dynamic', foreign_keys='Ticket.assigned_to')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    work_logs = db.relationship('WorkLog', backref='technician', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def is_technician(self):
        return self.role in ('technician', 'admin')

    def is_employee(self):
        return self.role == 'employee'

    def __repr__(self):
        return f'<User {self.email}>'
