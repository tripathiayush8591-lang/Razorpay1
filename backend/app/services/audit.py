import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


def log_audit_event(
    db: Session,
    actor_type: str,
    action: str,
    entity_type: str,
    session_id: Optional[str] = None,
    merchant_id: Optional[str] = None,
    entity_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    """Helper to record an authoritative audit trail event into SQLite."""
    event_id = f"audit_{uuid.uuid4().hex[:16]}"
    metadata_str = json.dumps(metadata or {})
    event = AuditEvent(
        id=event_id,
        merchant_id=merchant_id,
        session_id=session_id,
        actor_type=actor_type,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata_str,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()
    return event
