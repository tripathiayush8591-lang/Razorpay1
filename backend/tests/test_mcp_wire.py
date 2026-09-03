import json
import anyio
import pytest
import httpx
from app.main import app
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client


def test_mcp_streamable_http_protocol_lifecycle():
    """Verify official MCP Client connecting over Streamable HTTP transport against /mcp/."""
    async def run_protocol_test():
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://localhost:8000",
            ) as http_client:
                async with streamable_http_client(
                    "http://localhost:8000/mcp/",
                    http_client=http_client,
                ) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        # 1. initialize
                        init_res = await session.initialize()
                        assert init_res.server_info.name == "runcraft-commerce"

                        # 2. tools/list
                        tools_res = await session.list_tools()
                        tool_names = {t.name for t in tools_res.tools}
                        expected_tools = {
                            "search_products",
                            "get_product",
                            "check_inventory",
                            "get_delivery_estimate",
                            "get_offers",
                            "create_cart",
                            "add_to_cart",
                            "remove_from_cart",
                            "get_cart",
                            "get_final_quote",
                            "create_checkout",
                            "get_order",
                            "get_order_status",
                        }
                        assert expected_tools.issubset(tool_names)
                        assert len(tools_res.tools) == 13

                        # 3. tools/call search_products
                        search_call = await session.call_tool("search_products", {"query": "running"})
                        assert len(search_call.content) > 0
                        search_data = json.loads(search_call.content[0].text)
                        assert search_data["count"] > 0
                        chosen_prod_id = search_data["products"][0]["id"]

                        # 4. tools/call cart + quote sequence
                        import uuid
                        session_id = f"mcp_wire_{uuid.uuid4().hex[:8]}"
                        cart_call = await session.call_tool("create_cart", {"session_id": session_id})
                        cart_data = json.loads(cart_call.content[0].text)
                        cart_id = cart_data["id"]

                        add_call = await session.call_tool("add_to_cart", {
                            "session_id": session_id,
                            "cart_id": cart_id,
                            "product_id": chosen_prod_id,
                            "quantity": 1,
                        })
                        add_data = json.loads(add_call.content[0].text)
                        assert len(add_data["items"]) == 1

                        quote_call = await session.call_tool("get_final_quote", {
                            "session_id": session_id,
                            "cart_id": cart_id,
                        })
                        quote_data = json.loads(quote_call.content[0].text)
                        assert quote_data["valid"] is True
                        assert quote_data["total_paise"] > 0

    anyio.run(run_protocol_test)
