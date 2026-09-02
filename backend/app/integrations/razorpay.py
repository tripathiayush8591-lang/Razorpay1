import hmac
import hashlib
import logging
from typing import Any, Dict, Optional
import razorpay
from razorpay.errors import SignatureVerificationError, BadRequestError

from app.core.config import settings

logger = logging.getLogger(__name__)


class RazorpayIntegrationError(Exception):
    """Custom domain exception for Razorpay provider failures."""
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class RazorpayClientWrapper:
    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = webhook_secret or settings.RAZORPAY_WEBHOOK_SECRET
        self._client: Optional[razorpay.Client] = None

    @property
    def client(self) -> razorpay.Client:
        if self._client is None:
            if not self.key_id or not self.key_secret:
                raise RazorpayIntegrationError("Razorpay credentials are not configured", status_code=500)
            self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
        return self._client

    def create_order(
        self,
        amount_paise: int,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Creates a Razorpay Order server-side.
        Amount must be integer paise.
        """
        if amount_paise <= 0:
            raise RazorpayIntegrationError("Order amount must be greater than zero", status_code=400)

        data = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt or "",
            "notes": notes or {},
        }
        try:
            order_response = self.client.order.create(data=data)
            return order_response
        except BadRequestError as e:
            logger.error("Razorpay order creation bad request: %s", str(e))
            raise RazorpayIntegrationError(f"Razorpay order creation failed: {str(e)}", status_code=400)
        except Exception as e:
            logger.error("Razorpay order creation error: %s", str(e))
            raise RazorpayIntegrationError("Failed to initiate order with Razorpay gateway", status_code=502)

    def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Fetches live payment details from Razorpay to verify authoritative provider state (e.g. captured).
        """
        try:
            return self.client.payment.fetch(payment_id)
        except Exception as e:
            logger.error("Razorpay payment fetch error for %s: %s", payment_id, str(e))
            raise RazorpayIntegrationError(f"Could not verify payment status with Razorpay: {str(e)}", status_code=502)

    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """
        Server-side cryptographic verification of Razorpay payment signature.
        Generated signature = HMAC-SHA256(order_id + "|" + payment_id, secret)
        """
        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            return False

        try:
            self.client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })
            return True
        except SignatureVerificationError:
            logger.warning("Invalid payment signature for order %s, payment %s", razorpay_order_id, razorpay_payment_id)
            return False
        except Exception as e:
            logger.error("Error during signature verification: %s", str(e))
            return False

    def verify_webhook_signature(
        self,
        body_bytes: bytes,
        signature_header: str,
    ) -> bool:
        """
        Validates the incoming webhook signature against RAW request body bytes.
        """
        if not signature_header or not self.webhook_secret:
            return False

        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode("utf-8"),
                body_bytes,
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signature_header)
        except Exception as e:
            logger.error("Error verifying webhook signature: %s", str(e))
            return False


# Shared singleton instance
razorpay_client = RazorpayClientWrapper()
