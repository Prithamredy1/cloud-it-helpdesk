
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# Initialize extensions
db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Import models to register database tables
    from app.models.user import User
    from app.models.ticket import (
        Ticket,
        Category,
        Comment,
        WorkLog,
        Assignment,
        SLAPolicy,
        KnowledgeArticle,
        AuditLog
    )

    # Load authenticated users
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    # Import application blueprints
    from app.auth.routes import auth_bp
    from app.employee.routes import employee_bp
    from app.technician.routes import technician_bp
    from app.admin.routes import admin_bp
    from app.tickets.routes import tickets_bp

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_bp, url_prefix='/employee')
    app.register_blueprint(technician_bp, url_prefix='/technician')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(tickets_bp, url_prefix='/tickets')

    return app
