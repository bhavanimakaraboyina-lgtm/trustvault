
import pytest
from app import create_app
from app.extensions import db
from app.models import User, Document


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

        owner = User(
            name="Owner",
            email="owner@test.com",
            password_hash="test"
        )
        stranger = User(
            name="Stranger",
            email="stranger@test.com",
            password_hash="test"
        )

        db.session.add_all([owner, stranger])
        db.session.flush()

        document = Document(
            original_filename="private.txt",
            stored_filename="private-test.txt",
            owner_id=owner.id
        )

        db.session.add(document)
        db.session.commit()

        yield test_app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()



def login(client, email):
    with client.application.app_context():
        user = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one()

        user_id = str(user.id)

    with client.session_transaction() as session:
        session["_user_id"] = user_id
        session["_fresh"] = True

def test_stranger_cannot_download_document(client):
    login(client, "stranger@test.com")

    response = client.get("/download/1")

    assert response.status_code == 404


def test_stranger_cannot_edit_document(client):
    login(client, "stranger@test.com")

    response = client.post("/edit/1", data={
        "filename": "changed.txt",
        "category": "Personal"
    })

    assert response.status_code == 404
def test_stranger_cannot_delete_document(client):
    login(client, "stranger@test.com")

    response = client.post("/delete/1")

    assert response.status_code == 403

    with client.application.app_context():
        document = db.session.get(Document, 1)
        assert document.is_deleted is False


def test_owner_can_delete_document(client, monkeypatch):
    login(client, "owner@test.com")

    monkeypatch.setattr(
        "app.routes.documents.delete_document",
        lambda stored_name: True
    )

    response = client.post("/delete/1")

    assert response.status_code == 302

    with client.application.app_context():
        document = db.session.get(Document, 1)
        assert document.is_deleted is True