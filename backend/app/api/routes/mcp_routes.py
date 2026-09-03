import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.mcp.server import mcp_server
from app.schemas.common import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


class MCPToolSchemaInfo(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class ExecuteToolRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the MCP tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments dictionary for the tool")


class ExecuteToolResponse(BaseModel):
    tool_name: str
    is_error: bool
    result: Any


@router.get("/tools", response_model=ApiResponse[List[MCPToolSchemaInfo]])
async def list_mcp_tools():
    """
    List all registered MCP tools and their parameter schemas.
    Used by the external buyer client UI and admin channels inspector.
    """
    tools = await mcp_server.list_tools()
    tool_infos = [
        MCPToolSchemaInfo(
            name=t.name,
            description=t.description or "",
            input_schema=t.input_schema or {},
        )
        for t in tools
    ]
    return ApiResponse(data=tool_infos)


@router.post("/execute", response_model=ApiResponse[ExecuteToolResponse])
async def execute_mcp_tool(req: ExecuteToolRequest):
    """
    Execute an MCP tool directly via the MCPServer instance.
    Enables interactive browser-based testing for the External AI Buyer demo.
    """
    try:
        call_result = await mcp_server.call_tool(req.tool_name, req.arguments)
        
        # Extract content text or structured payload
        parsed_result: Any = None
        if call_result.content:
            first_content = call_result.content[0]
            if hasattr(first_content, "text"):
                try:
                    parsed_result = json.loads(first_content.text)
                except Exception:
                    parsed_result = first_content.text
            else:
                parsed_result = str(first_content)
        elif call_result.structured_content is not None:
            parsed_result = call_result.structured_content

        return ApiResponse(
            data=ExecuteToolResponse(
                tool_name=req.tool_name,
                is_error=call_result.is_error or False,
                result=parsed_result,
            )
        )
    except Exception as e:
        logger.error("Failed to execute MCP tool %s: %s", req.tool_name, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MCP tool execution failed: {str(e)}",
        )
