
from datetime import datetime, timezone

from app.extensions import db
from app.models import DocumentPermission


def has_document_permission(user, document, required_permission="read"):
    if not user or not user.is_authenticated:
        return False

    if not document or document.is_deleted:
        return False

    if required_permission not in ("read", "edit"):
        return False

    # Admin accounts do not automatically access confidential documents.
    if user.role == "admin":
        return False

    # Only document owners can automatically manage their own documents.
    if document.owner_id == user.id:
        return user.role == "owner"

    # Only registered Owner and Viewer accounts can receive shared access.
    if user.role not in ("owner", "viewer"):
        return False

    permission = db.session.execute(
        db.select(DocumentPermission).filter_by(
            document_id=document.id,
            user_id=user.id
        )
    ).scalar_one_or_none()

    if permission is None:
        return False

    # Reject expired permissions.
    if permission.expires_at:
        expiry = permission.expires_at

        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        if expiry <= datetime.now(timezone.utc):
            return False

    if required_permission == "read":
        return permission.permission in ("read", "edit")

    return permission.permission == "edit"


def can_read_document(user, document):
    return has_document_permission(user, document, "read")


def can_edit_document(user, document):
    return has_document_permission(user, document, "edit")
