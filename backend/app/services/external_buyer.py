import json
import logging
import time
from typing import Any, Dict, List, Optional
import httpx
from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.agent import ChatMessageTurn, ToolActivityItem
from app.schemas.external_buyer import (
    ExternalBuyerChatRequest,
    ExternalBuyerChatResponse,
    MCPToolCallRecord,
)
from app.schemas.quote import QuoteResponse
from app.integrations.gemini import is_gemini_available
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

logger = logging.getLogger(__name__)

EXTERNAL_BUYER_SYSTEM_PROMPT = """
You are an autonomous External AI Buyer purchasing agent operating on behalf of a shopper.
You do NOT work for the merchant. You interact with the merchant's commerce backend exclusively through Model Context Protocol (MCP) tools.

YOUR MISSION:
When a shopper specifies items or criteria, proactively discover matching products, check stock, assemble their cart, and fetch an authoritative merchant quote ready for human authorization.

CRITICAL OPERATIONAL RULES:
1. Search products via search_products and inspect details via get_product. Use concise keywords (e.g., "running" rather than full sentences).
2. Check inventory availability via check_inventory.
3. Assemble the cart: call create_cart and add_to_cart for the chosen item(s).
4. Call get_final_quote to calculate the authoritative merchant total including taxes and shipping rules.
5. MANDATORY HUMAN APPROVAL BOUNDARY: You must NEVER attempt to authorize payment or complete purchase on your own. Once get_final_quote is obtained, present a concise summary of the items and final total, explain that explicit human authorization is required, and STOP.
6. Keep your final response concise and objective. Do not output internal raw reasoning.
"""


class ExternalBuyerService:
    """
    Autonomous External AI Buyer orchestrator.
    Acts as a true MCP client over the Streamable HTTP transport against /mcp/.
    Has ZERO direct database access. All commerce operations route through MCP tools.
    """

    def __init__(self, session_id: str, cart_id: Optional[str] = None):
        self.session_id = session_id.strip()
        self.cart_id = cart_id.strip() if cart_id else None
        self.tool_activities: List[ToolActivityItem] = []
        self.mcp_calls: List[MCPToolCallRecord] = []
        self.active_quote: Optional[QuoteResponse] = None
        self.recommended_products: List[Dict[str, Any]] = []

    async def execute_turn(
        self,
        request: ExternalBuyerChatRequest,
        app_instance: Any,
    ) -> ExternalBuyerChatResponse:
        """Connect as an MCP client over Streamable HTTP and execute the buyer turn."""
        mcp_url = settings.MCP_STREAMABLE_HTTP_URL
        is_local_mcp_url = mcp_url.startswith("http://localhost") or mcp_url.startswith("http://127.0.0.1")
        transport = httpx.ASGITransport(app=app_instance) if is_local_mcp_url else None
        async with httpx.AsyncClient(transport=transport) as http_client:
            async with streamable_http_client(
                mcp_url,
                http_client=http_client,
            ) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as mcp_session:
                    # 1. Initialize MCP Session
                    await mcp_session.initialize()

                    # 2. Discover available tools over wire
                    tools_res = await mcp_session.list_tools()
                    logger.info(f"External Buyer discovered {len(tools_res.tools)} tools via MCP")

                    provider_used = "fallback"
                    final_text: Optional[str] = None

                    # 3. Attempt Gemini-driven autonomous agent
                    if is_gemini_available():
                        candidate_models = [settings.GEMINI_MODEL]
                        if "lite" not in settings.GEMINI_MODEL:
                            candidate_models.append("gemini-2.5-flash-lite")

                        for model_name in candidate_models:
                            try:
                                logger.info(f"Executing External AI Buyer turn with Gemini model {model_name}")
                                final_text = await self._run_gemini_buyer(
                                    mcp_session=mcp_session,
                                    message=request.message,
                                    history=request.history,
                                    model_name=model_name,
                                )
                                provider_used = "gemini"
                                break
                            except Exception as gemini_err:
                                err_str = str(gemini_err)
                                is_429 = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
                                if is_429 and model_name != candidate_models[-1]:
                                    logger.warning(
                                        f"Gemini model {model_name} quota exhausted (429); retrying with backup model {candidate_models[-1]}"
                                    )
                                    continue
                                logger.warning(
                                    f"Gemini External Buyer turn failed with model {model_name} ({gemini_err}); falling back to deterministic MCP buyer"
                                )
                                final_text = None
                                break

                    # 4. Deterministic MCP fallback if Gemini unavailable or failed
                    if final_text is None:
                        logger.info("Executing External AI Buyer turn with deterministic MCP fallback")
                        final_text = await self._run_deterministic_mcp_buyer(
                            mcp_session=mcp_session,
                            message=request.message,
                        )
                        provider_used = "mcp_fallback"

                    return ExternalBuyerChatResponse(
                        message=final_text or "Authoritative quote prepared via MCP. Human purchase authorization required.",
                        provider=provider_used,
                        tool_activity=self.tool_activities,
                        mcp_calls=self.mcp_calls,
                        recommendations=self.recommended_products,
                        cart_id=self.cart_id,
                        quote=self.active_quote,
                        approval_required=self.active_quote is not None,
                    )

    async def _call_mcp_tool(
        self,
        mcp_session: ClientSession,
        tool_name: str,
        arguments: Dict[str, Any],
        activity_label: str,
    ) -> Any:
        """Helper to invoke a tool over MCP Streamable HTTP and record wire activity."""
        start_time = time.time()
        try:
            call_res = await mcp_session.call_tool(tool_name, arguments)
            duration_ms = int((time.time() - start_time) * 1000)

            raw_text = call_res.content[0].text if call_res.content else "{}"
            try:
                parsed_result = json.loads(raw_text)
            except Exception:
                parsed_result = raw_text

            is_error = getattr(call_res, "is_error", False) or (
                isinstance(parsed_result, dict) and parsed_result.get("is_error") is True
            )

            self.mcp_calls.append(
                MCPToolCallRecord(
                    tool_name=tool_name,
                    arguments=arguments,
                    result=parsed_result,
                    is_error=is_error,
                    duration_ms=duration_ms,
                )
            )

            self.tool_activities.append(
                ToolActivityItem(
                    activity=activity_label,
                    status="failed" if is_error else "completed",
                    details=f"MCP: {tool_name}() ({duration_ms}ms)",
                )
            )

            return parsed_result
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.mcp_calls.append(
                MCPToolCallRecord(
                    tool_name=tool_name,
                    arguments=arguments,
                    result=str(e),
                    is_error=True,
                    duration_ms=duration_ms,
                )
            )
            self.tool_activities.append(
                ToolActivityItem(
                    activity=activity_label,
                    status="failed",
                    details=f"MCP error: {e}",
                )
            )
            raise

    async def _run_gemini_buyer(
        self,
        mcp_session: ClientSession,
        message: str,
        history: List[ChatMessageTurn],
        model_name: Optional[str] = None,
    ) -> str:
        """Run multi-turn dynamic function calling with Google Gemini over MCP client."""
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # Synchronous signature definitions used by google-genai for schema generation
        def search_products(query: str = "", category: str = "", max_price_paise: int = 0) -> dict:
            """Search products in the catalog by keyword, category, or maximum price in paise (1 INR = 100 paise)."""
            return {}

        def get_product(product_id: str) -> dict:
            """Retrieve details for a specific product ID."""
            return {}

        def check_inventory(product_id: str, quantity: int = 1) -> dict:
            """Check available warehouse stock for a product."""
            return {}

        def create_cart() -> dict:
            """Initialize a new shopping cart for this buyer session."""
            return {}

        def add_to_cart(product_id: str, quantity: int = 1) -> dict:
            """Add an item to the buyer's cart."""
            return {}

        def get_final_quote() -> dict:
            """Obtain an authoritative quote calculating live prices, inventory, delivery fees, and tax."""
            return {}

        gemini_tools = [
            search_products,
            get_product,
            check_inventory,
            create_cart,
            add_to_cart,
            get_final_quote,
        ]

        # Async dispatch implementations executed over real MCP client
        async def do_search_products(query: str = "", category: str = "", max_price_paise: int = 0) -> Dict[str, Any]:
            args: Dict[str, Any] = {}
            if query:
                args["query"] = query
            if category:
                args["category"] = category
            if max_price_paise > 0:
                args["max_price_paise"] = max_price_paise
            res = await self._call_mcp_tool(mcp_session, "search_products", args, f"Searching catalog for '{query or category}'")
            if isinstance(res, dict) and "products" in res:
                self.recommended_products = res["products"][:4]
            return res

        async def do_get_product(product_id: str) -> Dict[str, Any]:
            return await self._call_mcp_tool(mcp_session, "get_product", {"product_id": product_id}, f"Looking up product {product_id}")

        async def do_check_inventory(product_id: str, quantity: int = 1) -> Dict[str, Any]:
            return await self._call_mcp_tool(mcp_session, "check_inventory", {"product_id": product_id, "quantity": quantity}, f"Checking stock for {product_id}")

        async def do_create_cart() -> Dict[str, Any]:
            res = await self._call_mcp_tool(mcp_session, "create_cart", {"session_id": self.session_id}, "Creating server-owned cart")
            if isinstance(res, dict) and "id" in res:
                self.cart_id = res["id"]
            return res

        async def do_add_to_cart(product_id: str, quantity: int = 1) -> Dict[str, Any]:
            if not self.cart_id:
                await do_create_cart()
            res = await self._call_mcp_tool(
                mcp_session,
                "add_to_cart",
                {"session_id": self.session_id, "cart_id": self.cart_id, "product_id": product_id, "quantity": quantity},
                f"Adding item {product_id} to cart",
            )
            return res

        async def do_get_final_quote() -> Dict[str, Any]:
            if not self.cart_id:
                await do_create_cart()
            res = await self._call_mcp_tool(
                mcp_session,
                "get_final_quote",
                {"session_id": self.session_id, "cart_id": self.cart_id},
                "Generating authoritative quote",
            )
            if isinstance(res, dict) and "total_paise" in res:
                self.active_quote = QuoteResponse(**res)
            return res

        dispatch_map = {
            "search_products": do_search_products,
            "get_product": do_get_product,
            "check_inventory": do_check_inventory,
            "create_cart": do_create_cart,
            "add_to_cart": do_add_to_cart,
            "get_final_quote": do_get_final_quote,
        }

        # Build contents
        contents: List[Any] = []
        for turn in history[-4:]:
            role = "user" if turn.role == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=turn.content)]))
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))

        max_turns = 8
        final_text = ""

        for _ in range(max_turns):
            config = types.GenerateContentConfig(
                system_instruction=EXTERNAL_BUYER_SYSTEM_PROMPT,
                tools=gemini_tools,
                temperature=0.2,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )
            response = client.models.generate_content(
                model=model_name or settings.GEMINI_MODEL,
                contents=contents,
                config=config,
            )

            function_calls = response.function_calls
            if not function_calls:
                final_text = response.text or ""
                break

            # Process function calls emitted by Gemini
            turn_parts: List[Any] = []
            for call in function_calls:
                fn_name = call.name
                fn_args = dict(call.args) if call.args else {}
                if fn_name in dispatch_map:
                    fn_result = await dispatch_map[fn_name](**fn_args)
                    turn_parts.append(
                        types.Part.from_function_response(
                            name=fn_name,
                            response={"result": fn_result},
                        )
                    )

            # Append model turn and function responses
            contents.append(response.candidates[0].content)
            contents.append(types.Content(role="tool", parts=turn_parts))

        # Ensure authoritative quote is generated via MCP if cart was created with items
        if self.cart_id and self.active_quote is None:
            await do_get_final_quote()

        return final_text

    async def _run_deterministic_mcp_buyer(
        self,
        mcp_session: ClientSession,
        message: str,
    ) -> str:
        """
        Deterministic MCP buyer path when Gemini is offline or rate-limited.
        Dynamically extracts user constraints (budget, item types) from the prompt
        and interacts exclusively through real MCP tools.
        """
        import re

        msg_lower = message.lower()

        # 1. Parse budget from message
        budget_paise = 800000  # default 8,000 INR
        budget_matches = re.findall(r'(?:under|below|<|budget of|max(?:imum)? of)?\s*[₹Rs.]*\s*([0-9]+(?:,[0-9]+)*)', message, re.IGNORECASE)
        for match in budget_matches:
            try:
                num = int(match.replace(",", ""))
                if num > 100:  # Sensible INR amount
                    budget_paise = num * 100
                    break
            except Exception:
                pass

        # 2. Determine requested item categories from natural language
        wants_shoes = any(w in msg_lower for w in ["shoe", "shoes", "sneaker", "footwear", "runner", "trainer"])
        wants_socks = any(w in msg_lower for w in ["sock", "socks"])
        wants_apparel = any(w in msg_lower for w in ["shirt", "singlet", "short", "shorts", "apparel", "tee"])
        wants_accessories = any(w in msg_lower for w in ["cap", "flask", "bottle", "hydration", "belt"])
        is_kit = any(w in msg_lower for w in ["kit", "bundle", "set", "pack", "beginner", "combo"])

        selected_items: List[Dict[str, Any]] = []
        remaining_budget = budget_paise

        # A. Search for Shoes if requested or if kit was requested
        if wants_shoes or is_kit:
            shoe_res = await self._call_mcp_tool(
                mcp_session,
                "search_products",
                {"category": "Running Shoes", "max_price_paise": remaining_budget},
                f"Searching catalog for Running Shoes under ₹{remaining_budget // 100:,}",
            )
            shoes = shoe_res.get("products", []) if isinstance(shoe_res, dict) else []
            if shoes:
                chosen_shoe = None
                for s in shoes:
                    product_text = " ".join([
                        s.get("name", ""),
                        s.get("category", ""),
                        s.get("short_description", ""),
                    ]).lower()
                    if "beginner" in msg_lower and (
                        "daily trainer" in product_text
                        or "beginner" in product_text
                        or "budget" in product_text
                    ):
                        chosen_shoe = s
                        break
                    if "daily trainer" in product_text:
                        chosen_shoe = s
                        break
                if not chosen_shoe:
                    chosen_shoe = shoes[0]

                if chosen_shoe["price_paise"] <= remaining_budget:
                    selected_items.append(chosen_shoe)
                    remaining_budget -= chosen_shoe["price_paise"]

        # B. Search for Socks if requested
        if wants_socks:
            sock_res = await self._call_mcp_tool(
                mcp_session,
                "search_products",
                {"query": "socks", "max_price_paise": remaining_budget},
                f"Searching catalog for Running Socks under ₹{remaining_budget // 100:,}",
            )
            socks_list = sock_res.get("products", []) if isinstance(sock_res, dict) else []
            if socks_list:
                chosen_sock = socks_list[0]
                if chosen_sock["price_paise"] <= remaining_budget:
                    selected_items.append(chosen_sock)
                    remaining_budget -= chosen_sock["price_paise"]

        # C. Search for Accessories if requested
        if wants_accessories:
            acc_res = await self._call_mcp_tool(
                mcp_session,
                "search_products",
                {"category": "Hydration & Accessories", "max_price_paise": remaining_budget},
                f"Searching catalog for Accessories under ₹{remaining_budget // 100:,}",
            )
            accessories = acc_res.get("products", []) if isinstance(acc_res, dict) else []
            if accessories:
                chosen_acc = accessories[0]
                if chosen_acc["price_paise"] <= remaining_budget:
                    selected_items.append(chosen_acc)
                    remaining_budget -= chosen_acc["price_paise"]

        # D. Search for Apparel if requested
        if wants_apparel:
            app_res = await self._call_mcp_tool(
                mcp_session,
                "search_products",
                {"category": "Running Apparel", "max_price_paise": remaining_budget},
                f"Searching catalog for Apparel under ₹{remaining_budget // 100:,}",
            )
            apparel = app_res.get("products", []) if isinstance(app_res, dict) else []
            if apparel:
                chosen_app = apparel[0]
                if chosen_app["price_paise"] <= remaining_budget:
                    selected_items.append(chosen_app)
                    remaining_budget -= chosen_app["price_paise"]

        # Fallback to general search if no specific items matched
        if not selected_items:
            gen_res = await self._call_mcp_tool(
                mcp_session,
                "search_products",
                {"query": "running", "max_price_paise": budget_paise},
                f"Searching catalog for gear under ₹{budget_paise // 100:,}",
            )
            prods = gen_res.get("products", []) if isinstance(gen_res, dict) else []
            if prods:
                selected_items.append(prods[0])

        if not selected_items:
            return f"No matching products found under ₹{budget_paise // 100:,}."

        self.recommended_products = selected_items

        # 3. Check stock for each selected item
        for item in selected_items:
            await self._call_mcp_tool(
                mcp_session,
                "check_inventory",
                {"product_id": item["id"], "quantity": 1},
                f"Verifying stock for {item['name']}",
            )

        # 4. Create cart
        cart_res = await self._call_mcp_tool(
            mcp_session,
            "create_cart",
            {"session_id": self.session_id},
            "Creating buyer cart",
        )
        self.cart_id = cart_res.get("id")

        # 5. Add all selected items to cart
        for item in selected_items:
            await self._call_mcp_tool(
                mcp_session,
                "add_to_cart",
                {
                    "session_id": self.session_id,
                    "cart_id": self.cart_id,
                    "product_id": item["id"],
                    "quantity": 1,
                },
                f"Adding {item['name']} to cart",
            )

        # 6. Fetch authoritative quote (Stops at approval boundary!)
        quote_res = await self._call_mcp_tool(
            mcp_session,
            "get_final_quote",
            {"session_id": self.session_id, "cart_id": self.cart_id},
            "Fetching authoritative merchant quote",
        )
        if isinstance(quote_res, dict) and "total_paise" in quote_res:
            self.active_quote = QuoteResponse(**quote_res)

        items_summary = ", ".join(f"{it['name']} (₹{(it['price_paise'] / 100):,.2f})" for it in selected_items)
        quote_inr = (self.active_quote.total_paise / 100) if self.active_quote else (sum(it["price_paise"] for it in selected_items) / 100)
        return (
            f"I assembled your gear with: {items_summary}. "
            f"Warehouse inventory verified and cart prepared. The authoritative quote total is ₹{quote_inr:,.2f}. "
            f"External AI cannot autonomously execute payment. Please review and explicitly authorize the transaction."
        )
