
import pytest
from app import create_app
from app.extensions import db
from app.services.audit import record_audit_event, verify_audit_chain


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


def test_empty_audit_chain_is_valid(app):
    with app.app_context():
        valid, message = verify_audit_chain()
        assert valid is True


def test_valid_audit_chain(app):
    with app.app_context():
        record_audit_event(
            None, None, "UPLOAD", "SUCCESS", "File uploaded"
        )

        record_audit_event(
            None, None, "DOWNLOAD", "SUCCESS", "File downloaded"
        )

        db.session.commit()

        valid, message = verify_audit_chain()
        assert valid is True


def test_modified_audit_record_is_detected(app):
    with app.app_context():
        record = record_audit_event(
            None, None, "UPLOAD", "SUCCESS", "File uploaded"
        )

        db.session.commit()

        record.details = "Modified audit information"
        db.session.commit()

        valid, message = verify_audit_chain()

        assert valid is False
        assert "Tampering detected" in message
