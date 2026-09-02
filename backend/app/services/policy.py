import json
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.policy import MerchantPolicy
from app.schemas.policy import MerchantPolicyUpdateRequest


def get_merchant_policy(db: Session, merchant_id: str) -> MerchantPolicy:
    """Retrieve authoritative merchant policies for the given merchant ID."""
    policy = db.scalar(select(MerchantPolicy).where(MerchantPolicy.merchant_id == merchant_id))
    if not policy:
        # Create default policy if absent
        policy = MerchantPolicy(
            id=f"pol_{uuid.uuid4().hex[:12]}",
            merchant_id=merchant_id,
            max_discount_percent=15,
            allow_out_of_stock=False,
            require_purchase_approval=True,
            cross_sell_rules_json="[]",
            delivery_rules_json="{}",
            updated_at=datetime.now(timezone.utc),
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
    return policy


def update_merchant_policy(
    db: Session,
    merchant_id: str,
    data: MerchantPolicyUpdateRequest,
) -> MerchantPolicy:
    """Update policy guardrails and rules."""
    policy = get_merchant_policy(db, merchant_id)

    if data.max_discount_percent is not None:
        policy.max_discount_percent = data.max_discount_percent

    if data.allow_out_of_stock is not None:
        policy.allow_out_of_stock = data.allow_out_of_stock

    if data.require_purchase_approval is not None:
        policy.require_purchase_approval = data.require_purchase_approval

    if data.cross_sell_rules is not None:
        rules_dict = [r.model_dump() for r in data.cross_sell_rules]
        policy.cross_sell_rules_json = json.dumps(rules_dict)

    if data.delivery_rules is not None:
        policy.delivery_rules_json = json.dumps(data.delivery_rules.model_dump())

    policy.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(policy)
    return policy
