import hashlib
import json

from datetime import datetime, timezone

from app.extensions import db
from app.models import AuditLog


def record_audit_event(
    actor_id,
    document_id,
    action,
    outcome,
    details=None
):
    # Get the previous audit record
    previous = db.session.execute(
        db.select(AuditLog).order_by(AuditLog.id.desc()).limit(1)
    ).scalar_one_or_none()

    previous_hash = previous.entry_hash if previous else "GENESIS"

    # Create the new audit record
    log = AuditLog(
        actor_id=actor_id,
        document_id=document_id,
        action=action,
        outcome=outcome,
        details=details,
        previous_hash=previous_hash,
        created_at=datetime.now(timezone.utc)
    )

    db.session.add(log)
    db.session.flush()

    # Create a consistent record for hashing
    record = {
        "id": log.id,
        "actor_id": actor_id,
        "document_id": document_id,
        "action": action,
        "outcome": outcome,
        "details": details,
        "previous_hash": previous_hash,
        "created_at": log.created_at.isoformat()
    }

    record_data = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":")
    )

    # Generate SHA-256 hash
    log.entry_hash = hashlib.sha256(
        record_data.encode("utf-8")
    ).hexdigest()

    db.session.flush()

    return log

def verify_audit_chain():
    logs = db.session.execute(
        db.select(AuditLog).order_by(AuditLog.id.asc())
    ).scalars().all()

    expected_previous_hash = "GENESIS"

    for log in logs:

        if log.previous_hash != expected_previous_hash:
            return False, f"Chain broken at audit record {log.id}"

        created_at = log.created_at

        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        else:
            created_at = created_at.astimezone(timezone.utc)

        record = {
            "id": log.id,
            "actor_id": log.actor_id,
            "document_id": log.document_id,
            "action": log.action,
            "outcome": log.outcome,
            "details": log.details,
            "previous_hash": log.previous_hash,
            "created_at": created_at.isoformat()
        }

        record_data = json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":")
        )

        calculated_hash = hashlib.sha256(
            record_data.encode("utf-8")
        ).hexdigest()

        if calculated_hash != log.entry_hash:
            return False, f"Tampering detected at record {log.id}"

        expected_previous_hash = log.entry_hash

    return True, "All audit records are valid."
