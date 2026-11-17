
import os
from datetime import timedelta


class Config:
    # Detect production deployment
    IS_PRODUCTION = (
        os.environ.get('VERCEL') == '1'
        or os.environ.get('FLASK_ENV') == 'production'
    )

    # Secret key configuration
    SECRET_KEY = os.environ.get('SECRET_KEY')

    if not SECRET_KEY:
        if IS_PRODUCTION:
            raise RuntimeError(
                "SECRET_KEY environment variable must be configured in production."
            )
        SECRET_KEY = 'dev-secret-key-change-in-production-helpdesk-2024'

    # Database configuration
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or 'sqlite:///helpdesk.db'
    )

    # Normalize PostgreSQL URLs
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            'postgres://',
            'postgresql://',
            1
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Security settings
    WTF_CSRF_ENABLED = True

    # Application settings
    TICKETS_PER_PAGE = 20
