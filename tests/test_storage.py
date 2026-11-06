
import pytest
from io import BytesIO
from app import create_app
from app.services.storage import validate_file, delete_document


@pytest.fixture
def app():
    test_app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key"
    })

    yield test_app


def test_valid_text_file(app):
    with app.app_context():
        file = (BytesIO(b"Hello TrustVault"), "document.txt")
        assert validate_file(file_storage(file)) is True


def file_storage(data):
    from werkzeug.datastructures import FileStorage

    return FileStorage(
        stream=data[0],
        filename=data[1]
    )


def test_invalid_extension_rejected(app):
    with app.app_context():
        file = file_storage(
            (BytesIO(b"Hello"), "document.exe")
        )
        assert validate_file(file) is False


def test_invalid_pdf_signature_rejected(app):
    with app.app_context():
        file = file_storage(
            (BytesIO(b"Not a PDF file"), "document.pdf")
        )
        assert validate_file(file) is False


def test_invalid_text_encoding_rejected(app):
    with app.app_context():
        file = file_storage(
            (BytesIO(b"\xff\xfe\xfa"), "document.txt")
        )
        assert validate_file(file) is False


def test_path_traversal_filename_rejected(app):
    with app.app_context():
        assert delete_document("../important.txt") is False


def test_non_uuid_filename_rejected(app):
    with app.app_context():
        assert delete_document("document.txt") is False
