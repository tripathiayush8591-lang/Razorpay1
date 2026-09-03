"""
Model Context Protocol (MCP) server package for RunCraft Agentic Commerce.
Exposes commerce tools via Streamable HTTP and stdio transports.
"""

from app.mcp.server import mcp_server
import app.mcp.tools  # Register all 13 commerce tools on mcp_server

__all__ = ["mcp_server"]
