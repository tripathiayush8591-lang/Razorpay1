from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.checkout import PaymentVerifyRequest, PaymentVerifyResponse, WebhookResponse
from app.services.payment import PaymentService

router = APIRouter(tags=["payments"])


def resolve_session_id(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> str:
    if not x_session_id or not x_session_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session identifier is required via 'X-Session-ID' header",
        )
    return x_session_id.strip()


@router.post("/api/payments/razorpay/verify", response_model=ApiResponse[PaymentVerifyResponse])
def verify_payment_endpoint(
    payload: PaymentVerifyRequest,
    session_id: str = Depends(resolve_session_id),
    db: Session = Depends(get_db),
):
    """
    Verifies Razorpay payment signature server-side.
    Guarantees that payment state transitions to PAID and inventory decrements exactly once.
    """
    verification_res = PaymentService.verify_payment(
        db=db,
        payload=payload,
        session_id=session_id,
    )
    return ApiResponse(data=verification_res)


@router.post("/api/webhooks/razorpay", response_model=ApiResponse[WebhookResponse])
async def razorpay_webhook_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    x_razorpay_event_id: Optional[str] = Header(None, alias="X-Razorpay-Event-Id"),
):
    """
    Asynchronous Razorpay webhook handler.
    Validates raw HMAC-SHA256 signature and uses X-Razorpay-Event-Id for idempotent processing.
    """
    raw_body = await request.body()
    webhook_res = PaymentService.process_webhook(
        db=db,
        raw_body=raw_body,
        signature_header=x_razorpay_signature,
        event_id_header=x_razorpay_event_id,
    )
    return ApiResponse(data=webhook_res)
