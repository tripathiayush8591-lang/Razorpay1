import logging
from contextlib import contextmanager
from typing import Any, Dict, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from mcp.server.mcpserver import MCPServer
from app.db.session import SessionLocal
from app.models.merchant import Merchant
from app.services.audit import log_audit_event

logger = logging.getLogger(__name__)

# Official MCPServer instance for RunCraft Agentic Commerce
mcp_server = MCPServer(
    name="runcraft-commerce",
    description="RunCraft Agentic Commerce MCP Server - Authoritative commerce adapter for external AI buyers",
    version="1.0.0",
)


@contextmanager
def get_db_session():
    """Context manager providing an isolated database session for an MCP tool execution."""
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def format_mcp_error(exc: Exception) -> Dict[str, Any]:
    """Format exceptions into structured, informative MCP error responses."""
    if isinstance(exc, HTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            code = detail.get("code", "COMMERCE_ERROR")
            message = detail.get("message", str(detail))
            extra = {k: v for k, v in detail.items() if k not in ("code", "message")}
            err_dict = {"code": code, "message": message, "status_code": exc.status_code}
            if extra:
                err_dict.update(extra)
            return {"is_error": True, "error": err_dict}
        else:
            return {
                "is_error": True,
                "error": {
                    "code": "HTTP_ERROR",
                    "message": str(detail),
                    "status_code": exc.status_code,
                },
            }
    return {
        "is_error": True,
        "error": {
            "code": "INTERNAL_ERROR",
            "message": str(exc),
            "status_code": 500,
        },
    }


def record_mcp_audit(
    db: Session,
    session_id: Optional[str],
    tool_name: str,
    arguments: Dict[str, Any],
    success: bool,
    details: Optional[str] = None,
) -> None:
    """Record an authoritative audit entry for an external AI buyer tool execution."""
    try:
        merchant = db.scalar(select(Merchant).limit(1))
        merchant_id = merchant.id if merchant else "default_merchant"

        log_audit_event(
            db=db,
            merchant_id=merchant_id,
            session_id=session_id or "anonymous_mcp_session",
            actor_type="external_ai_buyer",
            action="mcp_tool_called",
            entity_type="mcp_tool",
            entity_id=tool_name,
            metadata={
                "tool": tool_name,
                "arguments": arguments,
                "success": success,
                "details": details,
            },
        )
    except Exception as e:
        logger.warning("Failed to record MCP audit event for %s: %s", tool_name, e)


def create_streamable_http_app():
    """Returns the official MCP Streamable HTTP ASGI app."""
    return mcp_server.streamable_http_app(streamable_http_path="/")


async def run_stdio():
    """Run the MCP server over standard input/output (for Claude Desktop / CLI)."""
    await mcp_server.run_stdio_async()


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_stdio())
