
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')

    if not SECRET_KEY:
        SECRET_KEY = 'dev-secret-key-change-in-production-helpdesk-2024'

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or 'sqlite:///helpdesk.db'
    )

    # Normalize PostgreSQL URLs if supplied by hosting providers.
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            'postgres://', 'postgresql://', 1
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    WTF_CSRF_ENABLED = True
    TICKETS_PER_PAGE = 20
