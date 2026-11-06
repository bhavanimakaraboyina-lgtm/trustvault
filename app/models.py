from datetime import datetime, timezone

from flask_login import UserMixin

from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), default="user", nullable=False)
    must_change_password = db.Column(
    db.Boolean, default=False, nullable=False
)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), unique=True, nullable=False)
    category = db.Column(db.String(100), default="General")
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    owner_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )

    uploaded_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    owner = db.relationship("User", foreign_keys=[owner_id])


class DocumentPermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    document_id = db.Column(
        db.Integer, db.ForeignKey("document.id"), nullable=False
    )

    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )

    permission = db.Column(db.String(10), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)

    document = db.relationship("Document")
    user = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint(
            "document_id", "user_id",
            name="unique_document_user_permission"
        ),
    )


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    actor_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=True
    )

    document_id = db.Column(
        db.Integer, db.ForeignKey("document.id"), nullable=True
    )

    action = db.Column(db.String(50), nullable=False)
    outcome = db.Column(db.String(20), nullable=False)
    details = db.Column(db.Text, nullable=True)

    previous_hash = db.Column(db.String(64), nullable=True)
    entry_hash = db.Column(db.String(64), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))