
import pytest

from app import create_app
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash


@pytest.fixture
def app():
    test_app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key"
    })

    with test_app.app_context():
        db.drop_all()
        db.create_all()

        yield test_app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_registration_success(client, app):
    response = client.post("/register", data={
        "name": "Test User",
        "email": "test@gmail.com",
        "password": "Password@123"
    })

    assert response.status_code == 302

    with app.app_context():
        user = db.session.execute(
            db.select(User).filter_by(email="test@gmail.com")
        ).scalar_one_or_none()

        assert user is not None
        assert user.role == "viewer"
        assert check_password_hash(user.password_hash, "Password@123")


def test_duplicate_email_registration(client, app):
    client.post("/register", data={
        "name": "First User",
        "email": "test@gmail.com",
        "password": "Password@123"
    })

    response = client.post("/register", data={
        "name": "Second User",
        "email": "test@gmail.com",
        "password": "Password@456"
    })

    assert response.status_code == 302

    with app.app_context():
        users = db.session.execute(
            db.select(User).filter_by(email="test@gmail.com")
        ).scalars().all()

        assert len(users) == 1


def test_short_password_rejected(client, app):
    response = client.post("/register", data={
        "name": "Test User",
        "email": "short@gmail.com",
        "password": "123"
    })

    assert response.status_code == 302

    with app.app_context():
        user = db.session.execute(
            db.select(User).filter_by(email="short@gmail.com")
        ).scalar_one_or_none()

        assert user is None


def test_login_success(client, app):
    with app.app_context():
        user = User(
            name="Test User",
            email="login@gmail.com",
            password_hash=generate_password_hash("Password@123"),
            role="owner"
        )
        db.session.add(user)
        db.session.commit()

    response = client.post("/login", data={
        "email": "login@gmail.com",
        "password": "Password@123",
        "login_role": "owner"
    })

    assert response.status_code == 302
    assert response.location.endswith("/")


def test_login_wrong_password(client, app):
    with app.app_context():
        user = User(
            name="Test User",
            email="login@gmail.com",
            password_hash=generate_password_hash("Password@123"),
            role="owner"
        )
        db.session.add(user)
        db.session.commit()

    response = client.post("/login", data={
        "email": "login@gmail.com",
        "password": "Wrong@123",
        "login_role": "owner"
    })

    assert response.status_code == 302
    assert response.location.endswith("/login")


def test_login_wrong_role_rejected(client, app):
    with app.app_context():
        user = User(
            name="Test User",
            email="viewer@gmail.com",
            password_hash=generate_password_hash("Password@123"),
            role="viewer"
        )
        db.session.add(user)
        db.session.commit()

    response = client.post("/login", data={
        "email": "viewer@gmail.com",
        "password": "Password@123",
        "login_role": "admin"
    })

    assert response.status_code == 302
    assert response.location.endswith("/login")


def test_login_without_role_rejected(client, app):
    response = client.post("/login", data={
        "email": "login@gmail.com",
        "password": "Password@123"
    })

    assert response.status_code == 302
    assert response.location.endswith("/login")
