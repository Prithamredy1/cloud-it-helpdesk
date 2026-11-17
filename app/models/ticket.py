
from app import db
from datetime import datetime, timedelta


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)

    tickets = db.relationship('Ticket', backref='category', lazy='dynamic')
    articles = db.relationship('KnowledgeArticle', backref='category', lazy='dynamic')


class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    request_type = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    priority = db.Column(db.String(20), default='Medium')
    status = db.Column(db.String(30), default='Open', index=True)
    affected_device = db.Column(db.String(120))
    location = db.Column(db.String(120))
    impact = db.Column(db.String(20), default='Medium')
    urgency = db.Column(db.String(20), default='Medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    first_response_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)

    comments = db.relationship(
        'Comment', backref='ticket', lazy='dynamic',
        cascade='all, delete-orphan'
    )
    work_logs = db.relationship(
        'WorkLog', backref='ticket', lazy='dynamic',
        cascade='all, delete-orphan'
    )
    assignments = db.relationship(
        'Assignment', backref='ticket', lazy='dynamic',
        cascade='all, delete-orphan'
    )
    audit_logs = db.relationship('AuditLog', backref='ticket', lazy='dynamic')

    def calculate_sla_status(self):
        from app.models.ticket import SLAPolicy

        policy = SLAPolicy.query.filter_by(
            priority=self.priority,
            is_active=True
        ).first()

        # Safety check: ensure policy and ticket creation time exist.
        if not policy or not self.created_at:
            return {
                'response_met': None,
                'resolution_met': None,
                'response_overdue': False,
                'resolution_overdue': False
            }

        now = datetime.utcnow()

        response_deadline = self.created_at + timedelta(
            minutes=policy.response_target_minutes
        )
        resolution_deadline = self.created_at + timedelta(
            minutes=policy.resolution_target_minutes
        )

        response_met = None
        if self.first_response_at:
            response_met = self.first_response_at <= response_deadline

        response_overdue = (
            (self.first_response_at is None and now > response_deadline)
            or (
                self.first_response_at is not None
                and self.first_response_at > response_deadline
            )
        )

        resolution_met = None
        if self.resolved_at:
            resolution_met = self.resolved_at <= resolution_deadline

        resolution_overdue = (
            (
                self.resolved_at is None
                and now > resolution_deadline
                and self.status not in ('Resolved', 'Closed')
            )
            or (
                self.resolved_at is not None
                and self.resolved_at > resolution_deadline
            )
        )

        return {
            'response_deadline': response_deadline,
            'resolution_deadline': resolution_deadline,
            'response_met': response_met,
            'resolution_met': resolution_met,
            'response_overdue': response_overdue,
            'resolution_overdue': resolution_overdue,
            'response_target_min': policy.response_target_minutes,
            'resolution_target_min': policy.resolution_target_minutes
        }


class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    reassignment_reason = db.Column(db.String(255))


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class WorkLog(db.Model):
    __tablename__ = 'work_logs'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_description = db.Column(db.Text, nullable=False)
    time_spent_minutes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SLAPolicy(db.Model):
    __tablename__ = 'sla_policies'

    id = db.Column(db.Integer, primary_key=True)
    priority = db.Column(db.String(20), unique=True, nullable=False)
    response_target_minutes = db.Column(db.Integer, nullable=False)
    resolution_target_minutes = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)


class KnowledgeArticle(db.Model):
    __tablename__ = 'knowledge_articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    problem_description = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    diagnostic_steps = db.Column(db.Text)
    resolution_steps = db.Column(db.Text)
    verification_steps = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'))
    action = db.Column(db.String(100), nullable=False)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
