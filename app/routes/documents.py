
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime, date, time, timezone
from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, send_file, abort, current_app
)
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Document, DocumentPermission, User, AuditLog
from app.services.permissions import can_read_document, can_edit_document
from app.services.storage import save_document, delete_document
from app.services.audit import record_audit_event, verify_audit_chain
from app.services.watermark import create_watermarked_copy

documents = Blueprint("documents", __name__)


# Dashboard
@documents.route("/")
@login_required
def dashboard():

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    upload_date = request.args.get("upload_date", "").strip()

    shared_access = and_(
        DocumentPermission.user_id == current_user.id,
        DocumentPermission.permission.in_(["read", "edit"]),
        or_(
            DocumentPermission.expires_at.is_(None),
            DocumentPermission.expires_at > db.func.current_timestamp()
        )
    )

    query = (
        db.select(Document)
        .join(User, Document.owner_id == User.id)
        .outerjoin(
            DocumentPermission,
            DocumentPermission.document_id == Document.id
        )
        .where(
            Document.is_deleted.is_(False),
            or_(
                Document.owner_id == current_user.id,
                shared_access
            )
        )
    )

    if search:
        query = query.where(
            or_(
                Document.original_filename.ilike(f"%{search}%"),
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )

    if category:
        query = query.where(Document.category == category)

    if upload_date:
        try:
            selected_date = date.fromisoformat(upload_date)
            query = query.where(
                db.func.date(Document.uploaded_at) == selected_date.isoformat()
            )
        except ValueError:
            flash("Invalid upload date.", "error")

    documents_list = db.session.execute(
        query.distinct()
    ).scalars().all()

    editable_document_ids = {
        document.id
        for document in documents_list
        if can_edit_document(current_user, document)
    }

    owned_document_ids = db.select(Document.id).where(
        Document.owner_id == current_user.id,
        Document.is_deleted.is_(False)
    )

    permissions = db.session.execute(
        db.select(DocumentPermission).where(
            DocumentPermission.document_id.in_(owned_document_ids)
        )
    ).scalars().all()

    permissions_by_document = {}

    for permission in permissions:
        permissions_by_document.setdefault(
            permission.document_id, []
        ).append(permission)

    # Get expiry information for documents shared with this user.
    shared_expiry_by_document = {}

    if documents_list:
        shared_permissions = db.session.execute(
            db.select(DocumentPermission).where(
                DocumentPermission.user_id == current_user.id,
                DocumentPermission.document_id.in_(
                    [document.id for document in documents_list]
                )
            )
        ).scalars().all()

        shared_expiry_by_document = {
            permission.document_id: permission.expires_at
            for permission in shared_permissions
        }

    # Find documents downloaded by this user before deletion.
    DownloadLog = aliased(AuditLog)
    DeleteLog = aliased(AuditLog)

    warning_rows = db.session.execute(
        db.select(
            Document,
            DownloadLog.created_at,
            DeleteLog.created_at
        )
        .join(
            DownloadLog,
            and_(
                DownloadLog.document_id == Document.id,
                DownloadLog.actor_id == current_user.id,
                DownloadLog.action == "DOWNLOAD",
                DownloadLog.outcome == "SUCCESS"
            )
        )
        .join(
            DeleteLog,
            and_(
                DeleteLog.document_id == Document.id,
                DeleteLog.action == "DELETE",
                DeleteLog.outcome == "SUCCESS",
                DeleteLog.created_at >= DownloadLog.created_at
            )
        )
        .where(Document.is_deleted.is_(True))
        .order_by(DeleteLog.created_at.desc())
    ).all()

    # Find warnings already dismissed by this user.
    dismissed_document_ids = set(
        db.session.execute(
            db.select(AuditLog.document_id).where(
                AuditLog.actor_id == current_user.id,
                AuditLog.action == "WARNING_DISMISSED",
                AuditLog.outcome == "SUCCESS"
            )
        ).scalars().all()
    )

    downloaded_copy_warnings = []
    seen_documents = set()

    for document, downloaded_at, deleted_at in warning_rows:

        if (
            document.id not in seen_documents
            and document.id not in dismissed_document_ids
        ):
            downloaded_copy_warnings.append({
                "id": document.id,
                "filename": document.original_filename,
                "downloaded_at": downloaded_at,
                "deleted_at": deleted_at
            })

            seen_documents.add(document.id)

    return render_template(
        "dashboard.html",
        documents=documents_list,
        permissions_by_document=permissions_by_document,
        shared_expiry_by_document=shared_expiry_by_document,
        search=search,
        category=category,
        upload_date=upload_date,
        editable_document_ids=editable_document_ids,
        downloaded_copy_warnings=downloaded_copy_warnings
    )


# Dismiss downloaded copy warning
@documents.route(
    "/warning/dismiss/<int:document_id>",
    methods=["POST"]
)
@login_required
def dismiss_download_warning(document_id):

    document = db.session.get(Document, document_id)

    if document is None or not document.is_deleted:
        abort(404)

    download_log = db.session.execute(
        db.select(AuditLog)
        .where(
            AuditLog.document_id == document_id,
            AuditLog.actor_id == current_user.id,
            AuditLog.action == "DOWNLOAD",
            AuditLog.outcome == "SUCCESS"
        )
        .order_by(AuditLog.created_at.desc())
    ).scalars().first()

    if download_log is None:
        abort(403)

    delete_log = db.session.execute(
        db.select(AuditLog)
        .where(
            AuditLog.document_id == document_id,
            AuditLog.action == "DELETE",
            AuditLog.outcome == "SUCCESS",
            AuditLog.created_at >= download_log.created_at
        )
        .order_by(AuditLog.created_at.desc())
    ).scalars().first()

    if delete_log is None:
        abort(403)

    already_dismissed = db.session.execute(
        db.select(AuditLog.id).where(
            AuditLog.document_id == document_id,
            AuditLog.actor_id == current_user.id,
            AuditLog.action == "WARNING_DISMISSED",
            AuditLog.outcome == "SUCCESS"
        )
    ).scalar_one_or_none()

    if already_dismissed is None:
        record_audit_event(
            current_user.id,
            document_id,
            "WARNING_DISMISSED",
            "SUCCESS",
            "User dismissed downloaded copy warning"
        )

        db.session.commit()

    flash("Warning dismissed successfully.", "success")

    return redirect(url_for("documents.dashboard"))


# Upload document
@documents.route("/upload", methods=["POST"])
@login_required
def upload_document():

    uploaded_file = request.files.get("document")
    category = request.form.get("category", "General").strip()

    if not uploaded_file or not uploaded_file.filename:
        flash("Please select a document.", "error")
        return redirect(url_for("documents.dashboard"))

    stored_name = None

    try:
        original_name, stored_name = save_document(uploaded_file)

        document = Document(
            original_filename=original_name,
            stored_filename=stored_name,
            category=category or "General",
            owner_id=current_user.id
        )

        db.session.add(document)
        db.session.flush()

        record_audit_event(
            current_user.id,
            document.id,
            "UPLOAD",
            "SUCCESS",
            "Document uploaded"
        )

        db.session.commit()
        flash("Document uploaded successfully.", "success")

    except ValueError as error:
        db.session.rollback()
        flash(str(error), "error")

    except Exception:
        db.session.rollback()

        if stored_name:
            delete_document(stored_name)

        current_app.logger.exception("Document upload failed")
        flash("Upload failed. Please try again.", "error")

    return redirect(url_for("documents.dashboard"))


# Download document with LeakTrace watermark
@documents.route("/download/<int:document_id>")
@login_required
def download_document(document_id):

    document = db.session.get(Document, document_id)

    if document is None or document.is_deleted:
        abort(404)

    if not can_read_document(current_user, document):

        record_audit_event(
            current_user.id,
            document.id,
            "DOWNLOAD",
            "DENIED",
            "User does not have read permission"
        )
        db.session.commit()

        abort(404)

    storage_folder = (
        Path(current_app.root_path).parent / "private_storage"
    )

    file_path = storage_folder / document.stored_filename

    if not file_path.is_file():
        abort(404)

    try:
        watermarked_file, tracking_id = create_watermarked_copy(
            file_path
        )

        record_audit_event(
            current_user.id,
            document.id,
            "DOWNLOAD",
            "SUCCESS",
            (
                "TrustVault logo watermark applied"
                if tracking_id is None
                else f"LeakTrace watermark applied. Reference: {tracking_id}"
            )
        )

        db.session.commit()

        return send_file(
            watermarked_file,
            as_attachment=True,
            download_name=document.original_filename
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Watermarked download failed")
        flash("Download failed. Please try again.", "error")
        return redirect(url_for("documents.dashboard"))


# Edit document details
@documents.route("/edit/<int:document_id>", methods=["POST"])
@login_required
def edit_document(document_id):

    document = db.session.get(Document, document_id)

    if document is None or document.is_deleted:
        abort(404)

    if not can_edit_document(current_user, document):
        record_audit_event(
            current_user.id,
            document.id,
            "EDIT",
            "DENIED",
            "User does not have edit permission"
        )
        db.session.commit()
        abort(404)

    new_filename = secure_filename(
        request.form.get("filename", "").strip()
    )
    new_category = request.form.get("category", "").strip()

    if (
        not new_filename
        or len(new_filename) > 255
        or Path(new_filename).suffix.lower()
        != Path(document.original_filename).suffix.lower()
        or not new_category
        or len(new_category) > 100
    ):
        flash("Invalid filename or category.", "error")
        return redirect(url_for("documents.dashboard"))

    document.original_filename = new_filename
    document.category = new_category

    record_audit_event(
        current_user.id,
        document.id,
        "EDIT",
        "SUCCESS",
        "Document filename and category updated"
    )

    db.session.commit()

    flash("Document details updated successfully!", "success")

    return redirect(url_for("documents.dashboard"))


# Delete document (owner only)
@documents.route("/delete/<int:document_id>", methods=["POST"])
@login_required
def delete_document_route(document_id):

    document = db.session.get(Document, document_id)

    if document is None or document.is_deleted:
        abort(404)

    if document.owner_id != current_user.id:

        record_audit_event(
            current_user.id,
            document.id,
            "DELETE",
            "DENIED",
            "Only the owner can delete this document"
        )
        db.session.commit()

        abort(403)

    stored_name = document.stored_filename

    try:
        if not delete_document(stored_name):
            raise OSError("Stored document could not be deleted")

        document.is_deleted = True

        record_audit_event(
            current_user.id,
            document.id,
            "DELETE",
            "SUCCESS",
            "Document deleted by owner"
        )

        db.session.commit()
        flash("Document deleted successfully.", "success")

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Document deletion failed")
        flash("Could not delete the document.", "error")

    return redirect(url_for("documents.dashboard"))


# Share document
@documents.route("/share/<int:document_id>", methods=["POST"])
@login_required
def share_document(document_id):

    document = db.session.get(Document, document_id)

    if document is None or document.is_deleted:
        abort(404)

    if document.owner_id != current_user.id:
        abort(403)

    email = request.form.get("email", "").strip().lower()
    permission_type = request.form.get("permission", "").strip()
    expiry_input = request.form.get("expiry", "").strip()

    if permission_type not in ("read", "edit"):
        flash("Select a valid permission.", "error")
        return redirect(url_for("documents.dashboard"))

    recipient = db.session.execute(
        db.select(User).where(User.email == email)
    ).scalar_one_or_none()

    if recipient is None:
        flash("No registered user found with that email.", "error")
        return redirect(url_for("documents.dashboard"))

    if recipient.id == current_user.id:
        flash("You already own this document.", "error")
        return redirect(url_for("documents.dashboard"))

    expiry = None

    if expiry_input:
        try:
            expiry_date = date.fromisoformat(expiry_input)

            if expiry_date <= date.today():
                raise ValueError

            expiry = datetime.combine(
                expiry_date,
                time.max,
                tzinfo=timezone.utc
            )

        except ValueError:
            flash("Enter a valid future expiry date.", "error")
            return redirect(url_for("documents.dashboard"))

    existing = db.session.execute(
        db.select(DocumentPermission).where(
            DocumentPermission.document_id == document.id,
            DocumentPermission.user_id == recipient.id
        )
    ).scalar_one_or_none()

    if existing:
        existing.permission = permission_type
        existing.expires_at = expiry
    else:
        existing = DocumentPermission(
            document_id=document.id,
            user_id=recipient.id,
            permission=permission_type,
            expires_at=expiry
        )
        db.session.add(existing)

    record_audit_event(
        current_user.id,
        document.id,
        "SHARE",
        "SUCCESS",
        f"Shared with {recipient.email}; permission={permission_type}"
    )

    db.session.commit()

    flash("Document access granted successfully.", "success")
    return redirect(url_for("documents.dashboard"))


# Revoke document access
@documents.route(
    "/revoke/<int:document_id>/<int:user_id>",
    methods=["POST"]
)
@login_required
def revoke_document_access(document_id, user_id):

    document = db.session.get(Document, document_id)

    if document is None or document.is_deleted:
        abort(404)

    if document.owner_id != current_user.id:
        abort(403)

    permission = db.session.execute(
        db.select(DocumentPermission).where(
            DocumentPermission.document_id == document_id,
            DocumentPermission.user_id == user_id
        )
    ).scalar_one_or_none()

    if permission is None:
        flash("No access permission found.", "error")
        return redirect(url_for("documents.dashboard"))

    recipient = db.session.get(User, user_id)

    recipient_email = recipient.email if recipient else "Unknown user"

    db.session.delete(permission)

    record_audit_event(
        current_user.id,
        document.id,
        "REVOKE",
        "SUCCESS",
        f"Access revoked for {recipient_email}"
    )

    db.session.commit()

    flash("Document access revoked successfully.", "success")

    return redirect(url_for("documents.dashboard"))


# Admin Audit Dashboard
@documents.route("/admin/audit")
@login_required
def admin_audit():

    if current_user.role != "admin":
        abort(403)

    audit_records = db.session.execute(
        db.select(
            AuditLog,
            User.name,
            User.email,
            Document.original_filename
        )
        .outerjoin(User, AuditLog.actor_id == User.id)
        .outerjoin(Document, AuditLog.document_id == Document.id)
        .order_by(AuditLog.id.desc())
    ).all()

    integrity_valid, integrity_message = verify_audit_chain()

    return render_template(
        "admin_audit.html",
        audit_records=audit_records,
        integrity_valid=integrity_valid,
        integrity_message=integrity_message
    )


# Admin User Management
@documents.route("/admin/users")
@login_required
def manage_users():

    if current_user.role != "admin":
        abort(403)

    users = db.session.execute(
        db.select(User).order_by(User.id)
    ).scalars().all()

    return render_template("admin_users.html", users=users)


# Admin Password Reset
@documents.route(
    "/admin/reset-password/<int:user_id>",
    methods=["POST"]
)
@login_required
def admin_reset_password(user_id):

    if current_user.role != "admin":
        abort(403)

    user = db.session.get(User, user_id)

    if user is None:
        abort(404)

    if user.id == current_user.id:
        flash("Use Change Password to update your own password.", "error")
        return redirect(url_for("documents.manage_users"))

    temporary_password = request.form.get("temporary_password", "")

    if (
        len(temporary_password) < 8
        or not any(c.isupper() for c in temporary_password)
        or not any(c.islower() for c in temporary_password)
        or not any(c.isdigit() for c in temporary_password)
        or not any(not c.isalnum() and not c.isspace() for c in temporary_password)
    ):
        flash("Temporary password must meet all password requirements.", "error")
        return redirect(url_for("documents.manage_users"))

    user.password_hash = generate_password_hash(temporary_password)
    user.must_change_password = True

    record_audit_event(
        current_user.id,
        None,
        "PASSWORD_RESET",
        "SUCCESS",
        f"Admin reset password for user ID {user.id}"
    )

    db.session.commit()

    flash("Temporary password set. The user must change it at next login.", "success")

    return redirect(url_for("documents.manage_users"))
