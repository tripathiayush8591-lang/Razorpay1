from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from app.schemas.product import ProductResponse
from app.schemas.cart import CartResponse
from app.schemas.quote import QuoteResponse


class ChatMessageTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ToolActivityItem(BaseModel):
    activity: str
    status: Literal["running", "completed", "failed"] = "completed"
    details: Optional[str] = None


class ProductRecommendationItem(BaseModel):
    product: ProductResponse
    reason: Optional[str] = None


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User prompt message")
    session_id: str = Field(..., min_length=1, description="Client/guest session ID")
    cart_id: Optional[str] = Field(None, description="Active cart ID if already initialized")
    history: List[ChatMessageTurn] = Field(default_factory=list, description="Recent conversation history")


class AgentChatResponse(BaseModel):
    message: str
    tool_activity: List[ToolActivityItem] = Field(default_factory=list)
    recommendations: List[ProductRecommendationItem] = Field(default_factory=list)
    cart: Optional[CartResponse] = None
    quote: Optional[QuoteResponse] = None
    approval_required: bool = False


# Direct Tool Request Schemas
class ToolSearchProductsRequest(BaseModel):
    q: Optional[str] = None
    category: Optional[str] = None
    max_price_paise: Optional[int] = None


class ToolGetProductRequest(BaseModel):
    product_id: str


class ToolAddToCartRequest(BaseModel):
    cart_id: str
    product_id: str
    quantity: int = Field(1, ge=1)


class ToolRemoveFromCartRequest(BaseModel):
    cart_id: str
    item_id: str


class ToolGetQuoteRequest(BaseModel):
    cart_id: str
