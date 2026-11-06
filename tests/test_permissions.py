from datetime import datetime, timedelta, timezone

from app.models import User, Document, DocumentPermission
from app.services.permissions import (
    can_read_document,
    can_edit_document
)
import pytest

from app import create_app
from app.extensions import db


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
def test_owner_can_read_and_edit(app):
    with app.app_context():
        owner = User(
            name="Owner",
            email="owner@test.com",
            password_hash="test"
        )
        db.session.add(owner)
        db.session.flush()

        document = Document(
            original_filename="test.txt",
            stored_filename="test-file.txt",
            owner_id=owner.id
        )
        db.session.add(document)
        db.session.commit()

        assert can_read_document(owner, document)
        assert can_edit_document(owner, document)


def test_unauthorized_user_cannot_access(app):
    with app.app_context():
        owner = User(
            name="Owner",
            email="owner@test.com",
            password_hash="test"
        )
        viewer = User(
            name="Viewer",
            email="viewer@test.com",
            password_hash="test"
        )
        db.session.add_all([owner, viewer])
        db.session.flush()

        document = Document(
            original_filename="test.txt",
            stored_filename="test-file.txt",
            owner_id=owner.id
        )
        db.session.add(document)
        db.session.commit()

        assert not can_read_document(viewer, document)
        assert not can_edit_document(viewer, document)


def test_read_only_user_cannot_edit(app):
    with app.app_context():
        owner = User(
            name="Owner",
            email="owner@test.com",
            password_hash="test"
        )
        viewer = User(
            name="Viewer",
            email="viewer@test.com",
            password_hash="test"
        )
        db.session.add_all([owner, viewer])
        db.session.flush()

        document = Document(
            original_filename="test.txt",
            stored_filename="test-file.txt",
            owner_id=owner.id
        )
        db.session.add(document)
        db.session.flush()

        permission = DocumentPermission(
            document_id=document.id,
            user_id=viewer.id,
            permission="read"
        )
        db.session.add(permission)
        db.session.commit()

        assert can_read_document(viewer, document)
        assert not can_edit_document(viewer, document)


def test_editor_can_edit(app):
    with app.app_context():
        owner = User(
            name="Owner",
            email="owner@test.com",
            password_hash="test"
        )
        editor = User(
            name="Editor",
            email="editor@test.com",
            password_hash="test"
        )
        db.session.add_all([owner, editor])
        db.session.flush()

        document = Document(
            original_filename="test.txt",
            stored_filename="test-file.txt",
            owner_id=owner.id
        )
        db.session.add(document)
        db.session.flush()

        permission = DocumentPermission(
            document_id=document.id,
            user_id=editor.id,
            permission="edit"
        )
        db.session.add(permission)
        db.session.commit()

        assert can_read_document(editor, document)
        assert can_edit_document(editor, document)


def test_expired_permission_is_rejected(app):
    with app.app_context():
        owner = User(
            name="Owner",
            email="owner@test.com",
            password_hash="test"
        )
        viewer = User(
            name="Viewer",
            email="viewer@test.com",
            password_hash="test"
        )
        db.session.add_all([owner, viewer])
        db.session.flush()

        document = Document(
            original_filename="test.txt",
            stored_filename="test-file.txt",
            owner_id=owner.id
        )
        db.session.add(document)
        db.session.flush()

        permission = DocumentPermission(
            document_id=document.id,
            user_id=viewer.id,
            permission="edit",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        db.session.add(permission)
        db.session.commit()

        assert not can_read_document(viewer, document)
        assert not can_edit_document(viewer, document)