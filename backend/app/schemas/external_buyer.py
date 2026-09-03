from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.agent import ChatMessageTurn, ToolActivityItem
from app.schemas.quote import QuoteResponse


class MCPToolCallRecord(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    is_error: bool = False
    duration_ms: Optional[int] = None


class ExternalBuyerChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Buyer natural language request")
    session_id: str = Field(..., min_length=1, description="External buyer session ID")
    cart_id: Optional[str] = Field(None, description="Current cart ID if known")
    history: List[ChatMessageTurn] = Field(default_factory=list, description="Recent conversation turns")


class ExternalBuyerChatResponse(BaseModel):
    message: str
    provider: str
    tool_activity: List[ToolActivityItem] = Field(default_factory=list)
    mcp_calls: List[MCPToolCallRecord] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    cart_id: Optional[str] = None
    quote: Optional[QuoteResponse] = None
    approval_required: bool = False
