from fastapi import APIRouter, Request, status
from app.schemas.common import ApiResponse
from app.schemas.external_buyer import (
    ExternalBuyerChatRequest,
    ExternalBuyerChatResponse,
)
from app.services.external_buyer import ExternalBuyerService

router = APIRouter(prefix="/external-buyer", tags=["External AI Buyer"])


@router.post(
    "/chat",
    response_model=ApiResponse[ExternalBuyerChatResponse],
    status_code=status.HTTP_200_OK,
    summary="Execute an External AI Buyer turn through real MCP Streamable HTTP",
)
async def external_buyer_chat(
    req: ExternalBuyerChatRequest,
    raw_request: Request,
):
    """
    Executes an autonomous External AI Buyer turn.
    The buyer service connects as an MCP Client over Streamable HTTP (/mcp/),
    dynamically queries MCP tools, drives Gemini function calling, and enforces
    the mandatory human approval boundary upon quote generation.
    """
    service = ExternalBuyerService(
        session_id=req.session_id,
        cart_id=req.cart_id,
    )
    result = await service.execute_turn(
        request=req,
        app_instance=raw_request.app,
    )
    return ApiResponse(
        success=True,
        data=result,
        error=None,
    )
