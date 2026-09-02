import json
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class CrossSellRule(BaseModel):
    trigger_category: str = Field(..., description="Category that triggers the cross-sell")
    recommend_category: str = Field(..., description="Category recommended to pair with trigger")
    reason: str = Field("", description="Contextual explanation shown to agent or buyer")


class DeliveryRules(BaseModel):
    free_delivery_threshold_paise: int = Field(200000, ge=0, description="Order subtotal for free delivery")
    standard_delivery_paise: int = Field(15000, ge=0, description="Standard delivery fee")
    express_delivery_paise: int = Field(35000, ge=0, description="Express delivery fee")
    estimated_days_standard: int = Field(3, ge=1, description="Standard delivery ETA in days")
    estimated_days_express: int = Field(1, ge=1, description="Express delivery ETA in days")


class MerchantPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    merchant_id: str
    max_discount_percent: int
    allow_out_of_stock: bool
    require_purchase_approval: bool
    cross_sell_rules: List[CrossSellRule]
    delivery_rules: DeliveryRules
    updated_at: datetime

    @classmethod
    def from_orm_model(cls, policy: Any) -> "MerchantPolicyResponse":
        try:
            cross_sell = (
                json.loads(policy.cross_sell_rules_json)
                if isinstance(policy.cross_sell_rules_json, str)
                else (policy.cross_sell_rules_json or [])
            )
        except Exception:
            cross_sell = []

        try:
            delivery = (
                json.loads(policy.delivery_rules_json)
                if isinstance(policy.delivery_rules_json, str)
                else (policy.delivery_rules_json or {})
            )
        except Exception:
            delivery = {}

        return cls(
            id=policy.id,
            merchant_id=policy.merchant_id,
            max_discount_percent=policy.max_discount_percent,
            allow_out_of_stock=policy.allow_out_of_stock,
            require_purchase_approval=policy.require_purchase_approval,
            cross_sell_rules=[CrossSellRule(**r) for r in cross_sell],
            delivery_rules=DeliveryRules(**delivery),
            updated_at=policy.updated_at,
        )


class MerchantPolicyUpdateRequest(BaseModel):
    max_discount_percent: Optional[int] = Field(None, ge=0, le=100)
    allow_out_of_stock: Optional[bool] = None
    require_purchase_approval: Optional[bool] = None
    cross_sell_rules: Optional[List[CrossSellRule]] = None
    delivery_rules: Optional[DeliveryRules] = None
