# Architecture Overview

## Three-Layer Design

1. **Presentation Layer**: Bootstrap 5 templates + minimal JavaScript
2. **Application Layer**: Flask blueprints (auth, employee, technician, admin)
3. **Data Layer**: SQLite via SQLAlchemy ORM

## Key Models
- User (roles: employee / technician / admin)
- Ticket (Incident or Service Request)
- WorkLog (troubleshooting history)
- SLAPolicy, KnowledgeArticle, AuditLog, Assignment, Comment, Category

## Request Flow
Browser → Flask route (permission check) → SQLAlchemy → SQLite → response template

## Security
- Password hashing (Werkzeug PBKDF2)
- Flask-Login sessions
- CSRF via Flask-WTF
- Role checks on every protected endpoint
