import pytest
from setu import create_app, db

@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    
    with app.app_context():
        db.create_all()  # Ensure the database is created for tests
        yield app
        db.session.remove()
        db.drop_all()  # Cleanup after tests

@pytest.fixture
def client(app):
    return app.test_client()
