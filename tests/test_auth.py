import pytest
from app import create_app, db
from app.models.user import User

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_login_page(client):
    rv = client.get('/login')
    assert rv.status_code == 200
    assert b'Sign in' in rv.data or b'Login' in rv.data or b'email' in rv.data
