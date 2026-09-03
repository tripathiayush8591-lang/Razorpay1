import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Bot,
  Terminal,
  ShieldCheck,
  CheckCircle,
  Play,
  RefreshCw,
  ShoppingCart,
  CreditCard,
  Sparkles,
  ExternalLink,
  Package,
  AlertCircle,
  AlertTriangle,
  Check,
  Lock,
  Zap,
} from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Input } from "../../components/ui/Input";
import { apiClient, resolveImageUrl } from "../../lib/api/client";
import { loadRazorpayScript } from "../../lib/razorpay";
import type {
  MCPToolSchemaInfo,
  MCPToolCallRecord,
  ToolActivityItem,
} from "../../types/domain";
import type { RazorpayOptions } from "../../types/razorpay";

export const ExternalBuyerPage: React.FC = () => {
  // MCP Connection State
  const [tools, setTools] = useState<MCPToolSchemaInfo[]>([]);
  const [loadingTools, setLoadingTools] = useState(true);
  const [showToolsRegistry, setShowToolsRegistry] = useState(false);

  // External Buyer Session State
  const [sessionId] = useState(() => `ext_buyer_${Math.random().toString(36).substring(2, 10)}`);
  const [cartId, setCartId] = useState<string | null>(null);

  // Workflow State
  const [queryPrompt, setQueryPrompt] = useState("Find beginner running shoes under ₹6,000 and prepare my quote for checkout");
  const [runningWorkflow, setRunningWorkflow] = useState(false);
  const [workflowStep, setWorkflowStep] = useState<
    "idle" | "searching" | "awaiting_approval" | "checkout_initiated" | "order_confirmed"
  >("idle");

  // Data artifacts from AI External Buyer turn
  const [agentMessage, setAgentMessage] = useState<string | null>(null);
  const [agentProvider, setAgentProvider] = useState<string | null>(null);
  const [toolActivities, setToolActivities] = useState<ToolActivityItem[]>([]);
  const [mcpWireCalls, setMcpWireCalls] = useState<MCPToolCallRecord[]>([]);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<any | null>(null);
  const [quoteData, setQuoteData] = useState<any | null>(null);
  const [checkoutData, setCheckoutData] = useState<any | null>(null);
  const [confirmedOrder, setConfirmedOrder] = useState<any | null>(null);

  // Approval / Customer Details Form
  const [customerName, setCustomerName] = useState("Aarav Sharma");
  const [customerEmail, setCustomerEmail] = useState("aarav.external@example.com");
  const [customerPhone, setCustomerPhone] = useState("+91 98765 43210");
  const [addressLine, setAddressLine] = useState("42 Indiranagar 100ft Road");
  const [city, setCity] = useState("Bengaluru");
  const [stateName, setStateName] = useState("Karnataka");
  const [postalCode, setPostalCode] = useState("560038");
  const [approvalError, setApprovalError] = useState<string | null>(null);

  // Interactive Tool Explorer (Debug Helper)
  const [selectedToolToTest, setSelectedToolToTest] = useState<string>("search_products");
  const [customToolArgs, setCustomToolArgs] = useState<string>("{}");
  const [testingTool, setTestingTool] = useState(false);
  const [toolTestResult, setToolTestResult] = useState<any | null>(null);

  // Fetch registered MCP tools on load
  useEffect(() => {
    async function fetchTools() {
      try {
        setLoadingTools(true);
        const res = await apiClient.getMcpTools();
        if (res.data) {
          setTools(res.data);
        }
      } catch (err) {
        console.error("Failed to load MCP tools:", err);
      } finally {
        setLoadingTools(false);
      }
    }
    fetchTools();
  }, []);

  // -------------------------------------------------------------------------
  // Execute Autonomous External AI Buyer Turn (Gemini over Streamable HTTP)
  // -------------------------------------------------------------------------
  const handleRunBuyerJourney = async () => {
    setRunningWorkflow(true);
    setWorkflowStep("searching");
    setSearchResults([]);
    setSelectedProduct(null);
    setQuoteData(null);
    setCheckoutData(null);
    setConfirmedOrder(null);
    setApprovalError(null);
    setAgentMessage(null);
    setToolActivities([]);
    setMcpWireCalls([]);

    try {
      // Connect to the autonomous External AI Buyer backend service.
      // The backend service acts as a real MCP Client over Streamable HTTP (/mcp/),
      // dynamically queries MCP tools, and runs Gemini function calling.
      const res = await apiClient.runExternalBuyerChat({
        message: queryPrompt,
        session_id: sessionId,
        cart_id: cartId || undefined,
        history: [],
      });

      if (!res.data) {
        throw new Error(res.error?.message || "No response received from External AI Buyer.");
      }

      const buyerData = res.data;
      setAgentProvider(buyerData.provider);
      setAgentMessage(buyerData.message);

      if (buyerData.mcp_calls && buyerData.mcp_calls.length > 0) {
        setMcpWireCalls(buyerData.mcp_calls);
      }

      if (buyerData.tool_activity && buyerData.tool_activity.length > 0) {
        setToolActivities(buyerData.tool_activity);
      }

      if (buyerData.recommendations && buyerData.recommendations.length > 0) {
        setSearchResults(buyerData.recommendations);
        setSelectedProduct(buyerData.recommendations[0]);
      }

      if (buyerData.cart_id) {
        setCartId(buyerData.cart_id);
      }

      if (buyerData.quote) {
        setQuoteData(buyerData.quote);
        // Explicit Human Approval Boundary Enforced!
        setWorkflowStep("awaiting_approval");
      } else {
        setWorkflowStep("idle");
      }
    } catch (err: any) {
      setApprovalError(err?.message || "External AI Buyer turn failed.");
      setWorkflowStep("idle");
    } finally {
      setRunningWorkflow(false);
    }
  };

  // -------------------------------------------------------------------------
  // Human Approval & Razorpay Test Checkout
  // -------------------------------------------------------------------------
  const handleExplicitApproveAndCheckout = async () => {
    if (!cartId || !quoteData) return;
    setApprovalError(null);
    setRunningWorkflow(true);

    try {
      // 1. Call create_checkout tool via MCP adapter
      const checkoutArgs = {
        session_id: sessionId,
        cart_id: cartId,
        approved_total_paise: quoteData.total_paise,
        customer_name: customerName,
        customer_email: customerEmail,
        customer_phone: customerPhone,
        shipping_address: {
          line1: addressLine,
          city,
          state: stateName,
          postal_code: postalCode,
          country: "India",
        },
      };

      const checkoutRes = await apiClient.executeMcpTool("create_checkout", checkoutArgs);

      if (checkoutRes.data?.is_error || checkoutRes.data?.result?.is_error) {
        const errMsg =
          checkoutRes.data?.result?.error?.message ||
          checkoutRes.data?.result?.error ||
          "Checkout creation failed.";
        throw new Error(typeof errMsg === "object" ? JSON.stringify(errMsg) : errMsg);
      }

      const checkoutPayload = checkoutRes.data?.result;
      setCheckoutData(checkoutPayload);
      setWorkflowStep("checkout_initiated");

      // 2. Load Razorpay script and open official modal
      const isLoaded = await loadRazorpayScript();
      if (!isLoaded || !window.Razorpay) {
        throw new Error("Failed to load Razorpay Checkout SDK.");
      }

      const options: RazorpayOptions = {
        key: checkoutPayload.razorpay_key_id,
        amount: checkoutPayload.amount_paise,
        currency: checkoutPayload.currency || "INR",
        name: "RunCraft (External AI Buyer)",
        description: "MCP Autonomous Channel Checkout",
        order_id: checkoutPayload.razorpay_order_id,
        prefill: {
          name: customerName,
          email: customerEmail,
          contact: customerPhone,
        },
        notes: {
          channel: "mcp_external_buyer",
          merchant_order_id: checkoutPayload.merchant_order_id,
        },
        theme: {
          color: "#7c5cfc",
        },
        handler: async (paymentResponse) => {
          try {
            setRunningWorkflow(true);

            // 3. Cryptographic payment verification
            await apiClient.verifyPayment(
              {
                merchant_order_id: checkoutPayload.merchant_order_id,
                razorpay_order_id: paymentResponse.razorpay_order_id,
                razorpay_payment_id: paymentResponse.razorpay_payment_id,
                razorpay_signature: paymentResponse.razorpay_signature,
              },
              sessionId
            );

            // 4. External AI Buyer calls get_order via MCP
            const orderArgs = {
              session_id: sessionId,
              order_id: checkoutPayload.merchant_order_id,
            };
            const orderRes = await apiClient.executeMcpTool("get_order", orderArgs);

            setConfirmedOrder(orderRes.data?.result);
            setWorkflowStep("order_confirmed");
          } catch (verErr: any) {
            setApprovalError(verErr?.message || "Payment verification failed.");
          } finally {
            setRunningWorkflow(false);
          }
        },
        modal: {
          ondismiss: () => {
            setRunningWorkflow(false);
          },
        },
      };

      const rzpInstance = new window.Razorpay(options);
      rzpInstance.open();
    } catch (err: any) {
      setApprovalError(err?.message || "Failed to initiate checkout via MCP.");
      setRunningWorkflow(false);
    }
  };

  // -------------------------------------------------------------------------
  // Debug Tool Tester Handler
  // -------------------------------------------------------------------------
  const handleTestSingleTool = async () => {
    setTestingTool(true);
    setToolTestResult(null);
    try {
      let parsedArgs: any = {};
      try {
        parsedArgs = JSON.parse(customToolArgs);
      } catch (e) {
        throw new Error("Invalid JSON arguments");
      }

      if (!parsedArgs.session_id && (selectedToolToTest.includes("cart") || selectedToolToTest.includes("quote") || selectedToolToTest.includes("checkout") || selectedToolToTest.includes("order"))) {
        parsedArgs.session_id = sessionId;
      }
      if (!parsedArgs.cart_id && cartId && (selectedToolToTest.includes("cart") || selectedToolToTest.includes("quote") || selectedToolToTest.includes("checkout"))) {
        parsedArgs.cart_id = cartId;
      }

      const res = await apiClient.executeMcpTool(selectedToolToTest, parsedArgs);
      setToolTestResult(res.data);
    } catch (err: any) {
      setToolTestResult({ is_error: true, error: err.message });
    } finally {
      setTestingTool(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-accent text-white flex items-center justify-center shadow-xs">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-text-primary">External AI Buyer Channel</h1>
              <p className="text-xs text-text-secondary mt-0.5">
                Autonomous Agent powered by Google Gemini &amp; Model Context Protocol (MCP)
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {workflowStep !== "idle" && (
            <Badge variant="info" className="text-[11px] py-1 px-2.5 capitalize">
              Step: {workflowStep.replace("_", " ")}
            </Badge>
          )}
          {agentProvider && (
            <Badge variant="accent" className="text-[11px] py-1 px-2.5">
              {agentProvider === "gemini" ? "✨ Gemini Autonomous Agent" : "⚡ MCP Deterministic Fallback"}
            </Badge>
          )}
          <Badge variant="accent" className="flex items-center gap-1.5 py-1 px-3">
            <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
            MCP Client: /mcp (Streamable HTTP)
          </Badge>
          <Badge variant="neutral" className="font-mono text-[11px] py-1 px-2.5">
            Session: {sessionId.substring(0, 16)}...
          </Badge>
        </div>
      </div>

      {/* Architectural Doctrine Banner */}
      <div className="bg-surface rounded-2xl border border-border p-5 shadow-xs flex items-start gap-4">
        <div className="w-9 h-9 rounded-xl bg-accent-light text-accent-dark flex items-center justify-center shrink-0">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <h3 className="text-sm font-bold text-text-primary">MCP Security Doctrine: External Agents Decide, Commerce Layer Enforces</h3>
          <p className="text-xs text-text-secondary leading-relaxed">
            The external AI agent operates without direct database access, dynamically discovering and invoking tools exclusively over the 
            <strong> official MCP Streamable HTTP transport</strong>. 
            <strong> AI intent or tool calls never count as human purchase approval.</strong> 
            The quote must be re-verified against live SQLite prices and inventory, and explicit human authorization is strictly mandatory before Razorpay checkout.
          </p>
        </div>
      </div>

      {/* Main Interactive Flow */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Buyer Prompt, Agent Action Summaries & Wire Trace (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Prompt Card */}
          <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-accent" />
                <h2 className="text-sm font-bold text-text-primary">Autonomous Buyer Prompt</h2>
              </div>
              <span className="text-[11px] text-text-muted">Hackathon Demo 3 Scenario</span>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-text-secondary">Buyer Instruction:</label>
              <div className="flex gap-2">
                <Input
                  value={queryPrompt}
                  onChange={(e) => setQueryPrompt(e.target.value)}
                  placeholder="e.g. Find beginner running shoes under ₹6,000 and prepare my quote for checkout"
                  className="text-xs font-mono"
                  disabled={runningWorkflow}
                />
                <Button
                  variant="primary"
                  onClick={handleRunBuyerJourney}
                  disabled={runningWorkflow || !queryPrompt.trim()}
                  icon={runningWorkflow ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                  className="shrink-0 text-xs px-4"
                >
                  {runningWorkflow ? "Orchestrating..." : "Run AI Buyer"}
                </Button>
              </div>
            </div>

            <div className="flex items-center gap-2 text-[11px] text-text-secondary pt-1 flex-wrap">
              <span>Quick Scenarios:</span>
              <button
                type="button"
                className="underline hover:text-accent font-mono text-[10px]"
                onClick={() => setQueryPrompt("Find beginner running shoes under ₹6,000 and prepare my quote for checkout")}
              >
                Shoes &lt; ₹6,000 (Road)
              </button>
              <span>•</span>
              <button
                type="button"
                className="underline hover:text-accent font-mono text-[10px]"
                onClick={() => setQueryPrompt("Find trail running shoes with grip and assemble a cart with quote")}
              >
                Trail Running Kit
              </button>
            </div>
          </div>

          {/* Agent Narrative Summary */}
          {agentMessage && (
            <div className="bg-surface rounded-2xl border border-accent/30 p-5 shadow-xs space-y-2 animate-in fade-in duration-200">
              <div className="flex items-center justify-between pb-2 border-b border-border/50">
                <div className="flex items-center gap-2">
                  <Bot className="w-4 h-4 text-accent" />
                  <span className="text-xs font-bold text-text-primary">External AI Buyer Statement</span>
                </div>
                <Badge variant="accent" className="text-[10px]">
                  {agentProvider === "gemini" ? "Autonomous Turn" : "Fallback Path"}
                </Badge>
              </div>
              <p className="text-xs text-text-primary leading-relaxed font-sans">{agentMessage}</p>
            </div>
          )}

          {/* Action Summaries (Concise Tool Decisions) */}
          {toolActivities.length > 0 && (
            <div className="bg-surface rounded-2xl border border-border p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-border">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-accent" />
                  <h3 className="text-xs font-bold text-text-primary">Agent Action Sequence</h3>
                </div>
                <span className="text-[10px] text-text-muted">{toolActivities.length} Actions Decided</span>
              </div>

              <div className="space-y-2">
                {toolActivities.map((act, idx) => (
                  <div key={idx} className="flex items-center justify-between text-xs py-1 px-2.5 rounded-lg bg-surface-secondary/50 border border-border/40">
                    <span className="font-medium text-text-primary">{act.activity}</span>
                    <Badge variant={act.status === "completed" ? "success" : "error"} className="text-[10px] font-mono">
                      {act.details}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Structured Recommendations from MCP Tool Calls */}
          {searchResults.length > 0 && (
            <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <div className="flex items-center gap-2">
                  <Package className="w-4 h-4 text-accent" />
                  <h3 className="text-sm font-bold text-text-primary">
                    MCP Tool Result: <code className="text-accent font-mono text-xs">search_products()</code>
                  </h3>
                </div>
                <span className="text-[11px] text-text-muted">{searchResults.length} Products Found</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {searchResults.map((prod) => {
                  const isSelected = selectedProduct?.id === prod.id;
                  return (
                    <div
                      key={prod.id}
                      className={`p-3.5 rounded-xl border transition-all text-xs flex gap-3 items-center ${
                        isSelected
                          ? "border-accent bg-accent-light/40 shadow-xs ring-1 ring-accent/30"
                          : "border-border bg-surface-secondary/40"
                      }`}
                    >
                      <img
                        src={resolveImageUrl(prod.image_url) || "/placeholder.png"}
                        alt={prod.name}
                        className="w-14 h-14 object-cover rounded-lg bg-surface border border-border shrink-0"
                      />
                      <div className="min-w-0 flex-1 space-y-0.5">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-text-primary truncate">{prod.name}</span>
                          {isSelected && <Check className="w-3.5 h-3.5 text-accent shrink-0 ml-1" />}
                        </div>
                        <p className="text-[10px] text-text-secondary truncate">{prod.category}</p>
                        <div className="flex items-center justify-between pt-1">
                          <span className="font-semibold text-text-primary">
                            ₹{(prod.price_paise / 100).toLocaleString("en-IN")}
                          </span>
                          <span className="text-[10px] text-success font-medium">
                            {prod.inventory_quantity} in stock
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Real MCP Streamable HTTP Wire Operations Log */}
          <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-accent" />
                <h3 className="text-sm font-bold text-text-primary">MCP Wire Protocol Log (/mcp/)</h3>
              </div>
              <span className="text-[11px] text-text-muted font-mono">{mcpWireCalls.length} Protocol Invocations</span>
            </div>

            {mcpWireCalls.length === 0 ? (
              <div className="py-8 text-center text-xs text-text-muted space-y-1">
                <Terminal className="w-6 h-6 mx-auto opacity-40 mb-2" />
                <p>No MCP protocol tool calls executed yet.</p>
                <p className="text-[11px]">Click "Run AI Buyer" to initiate live MCP client communication.</p>
              </div>
            ) : (
              <div className="space-y-3 font-mono text-xs max-h-96 overflow-y-auto pr-1">
                {mcpWireCalls.map((log, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-xl border ${
                      log.is_error
                        ? "bg-error-light border-error/20 text-error-foreground"
                        : "bg-surface-secondary/70 border-border/70 text-text-primary"
                    }`}
                  >
                    <div className="flex items-center justify-between pb-1.5 border-b border-border/40 text-[11px]">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-accent">{log.tool_name}()</span>
                        {log.duration_ms && <span className="text-[10px] text-text-muted">{log.duration_ms}ms</span>}
                      </div>
                      <Badge variant={log.is_error ? "error" : "success"} className="text-[9px] py-0 px-1.5">
                        {log.is_error ? "Failed" : "Success"}
                      </Badge>
                    </div>

                    <div className="mt-2 space-y-1 text-[11px]">
                      <div>
                        <span className="text-text-muted">Arguments: </span>
                        <span className="text-text-secondary">{JSON.stringify(log.arguments)}</span>
                      </div>
                      <div>
                        <span className="text-text-muted">Response: </span>
                        <span className="text-text-primary">
                          {typeof log.result === "object"
                            ? JSON.stringify(log.result).substring(0, 140) + (JSON.stringify(log.result).length > 140 ? "..." : "")
                            : String(log.result)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Authoritative Quote & Explicit Approval Boundary (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Approval Card (Mandatory Human Boundary) */}
          <div className="bg-surface rounded-2xl border-2 border-accent/40 p-6 shadow-sm space-y-5 relative overflow-hidden">
            <div className="absolute top-0 right-0 bg-accent text-white text-[10px] font-bold px-3 py-1 rounded-bl-xl uppercase tracking-wider flex items-center gap-1">
              <Lock className="w-3 h-3" />
              Human Boundary
            </div>

            <div>
              <h2 className="text-base font-bold text-text-primary flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-accent" />
                Explicit Purchase Authorization
              </h2>
              <p className="text-xs text-text-secondary mt-1">
                Authoritative quote generated via MCP <code className="text-accent">get_final_quote()</code>.
              </p>
            </div>

            {quoteData ? (
              <div className="space-y-4">
                {/* Itemized Line Items */}
                <div className="bg-surface-secondary/60 rounded-xl p-3.5 border border-border space-y-2 text-xs">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-text-muted">
                    Authoritative Cart Items ({quoteData.items?.length || 0})
                  </span>
                  {quoteData.items?.map((it: any) => (
                    <div key={it.product_id} className="flex justify-between items-center py-1 border-b border-border/50 last:border-0">
                      <div>
                        <p className="font-semibold text-text-primary">{it.name}</p>
                        <p className="text-[10px] text-text-muted">Qty: {it.quantity} × ₹{(it.unit_price_paise / 100).toLocaleString("en-IN")}</p>
                      </div>
                      <span className="font-bold text-text-primary">
                        ₹{(it.total_paise / 100).toLocaleString("en-IN")}
                      </span>
                    </div>
                  ))}

                  {/* Financial Breakdown */}
                  <div className="pt-2 space-y-1 text-xs border-t border-border">
                    <div className="flex justify-between text-text-secondary">
                      <span>Subtotal:</span>
                      <span>₹{(quoteData.subtotal_paise / 100).toLocaleString("en-IN")}</span>
                    </div>
                    <div className="flex justify-between text-text-secondary">
                      <span>Delivery:</span>
                      <span>
                        {quoteData.delivery_paise === 0 ? (
                          <span className="text-success font-semibold">FREE</span>
                        ) : (
                          `₹${(quoteData.delivery_paise / 100).toLocaleString("en-IN")}`
                        )}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm font-bold text-text-primary pt-1 border-t border-border">
                      <span>Approved Total:</span>
                      <span className="text-accent">
                        ₹{quoteData.total_inr?.toLocaleString("en-IN", { minimumFractionDigits: 2 }) || (quoteData.total_paise / 100).toLocaleString("en-IN")}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Customer Contact & Shipping Details */}
                <div className="space-y-2.5 pt-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-text-muted">
                    Buyer Delivery Info
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <Input
                      label="Customer Name"
                      value={customerName}
                      onChange={(e) => setCustomerName(e.target.value)}
                      className="text-xs"
                      disabled={runningWorkflow}
                    />
                    <Input
                      label="Phone"
                      value={customerPhone}
                      onChange={(e) => setCustomerPhone(e.target.value)}
                      className="text-xs"
                      disabled={runningWorkflow}
                    />
                  </div>
                  <Input
                    label="Email"
                    value={customerEmail}
                    onChange={(e) => setCustomerEmail(e.target.value)}
                    className="text-xs"
                    disabled={runningWorkflow}
                  />
                  <Input
                    label="Shipping Address"
                    value={addressLine}
                    onChange={(e) => setAddressLine(e.target.value)}
                    className="text-xs"
                    disabled={runningWorkflow}
                  />
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <Input
                      label="City"
                      value={city}
                      onChange={(e) => setCity(e.target.value)}
                      className="text-xs"
                      disabled={runningWorkflow}
                    />
                    <Input
                      label="State"
                      value={stateName}
                      onChange={(e) => setStateName(e.target.value)}
                      className="text-xs"
                      disabled={runningWorkflow}
                    />
                    <Input
                      label="PIN Code"
                      value={postalCode}
                      onChange={(e) => setPostalCode(e.target.value)}
                      className="text-xs"
                      disabled={runningWorkflow}
                    />
                  </div>
                </div>

                {checkoutData && (
                  <div className="p-3 rounded-xl bg-info-light/40 border border-info/30 text-xs space-y-1">
                    <p className="font-semibold text-text-primary">Razorpay Test Order Generated:</p>
                    <p className="font-mono text-[11px] text-text-secondary">
                      {checkoutData.razorpay_order_id} ({checkoutData.merchant_order_id})
                    </p>
                  </div>
                )}

                {/* Error Banner */}
                {approvalError && (
                  <div className="p-3 rounded-xl bg-error-light border border-error/20 text-error-foreground text-xs flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0 text-error" />
                    <span>{approvalError}</span>
                  </div>
                )}

                {/* Explicit Approval CTA */}
                <div className="pt-2">
                  <Button
                    variant="primary"
                    size="lg"
                    className="w-full text-xs font-bold py-3.5 shadow-sm"
                    onClick={handleExplicitApproveAndCheckout}
                    disabled={runningWorkflow || !quoteData.valid}
                    icon={<CreditCard className="w-4 h-4" />}
                  >
                    {runningWorkflow
                      ? "Processing Payment..."
                      : `Explicitly Approve & Pay ₹${(quoteData.total_paise / 100).toLocaleString("en-IN")}`}
                  </Button>
                  <p className="text-[10px] text-center text-text-muted mt-2">
                    External AI cannot initiate transactions. Human authorization required.
                  </p>
                </div>
              </div>
            ) : agentMessage && !runningWorkflow ? (
              <div className="py-8 text-center text-xs space-y-3 bg-warning-light border border-warning/20 rounded-xl p-5">
                <AlertTriangle className="w-7 h-7 mx-auto text-warning" />
                <p className="font-bold text-text-primary text-sm">Request Unfulfillable Under Current Constraints</p>
                <p className="text-xs max-w-xs mx-auto text-text-secondary leading-relaxed">
                  The AI buyer evaluated our live catalog via MCP, but could not assemble a valid quote matching your exact constraints.
                </p>
                <div className="pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setQueryPrompt("Find beginner running shoes under ₹6,000 and prepare my quote for checkout")}
                    className="text-xs"
                  >
                    Try Recommended Running Kit (₹6,000)
                  </Button>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-xs text-text-muted space-y-2">
                <ShoppingCart className="w-8 h-8 mx-auto opacity-30" />
                <p className="font-medium text-text-secondary">No Quote Awaiting Approval</p>
                <p className="text-[11px] max-w-xs mx-auto">
                  Run the External AI Buyer prompt above to have the agent discover products and assemble an authoritative quote.
                </p>
              </div>
            )}
          </div>

          {/* Order Result Card (After Payment Verification) */}
          {confirmedOrder && (
            <div className="bg-surface rounded-2xl border-2 border-success/40 p-6 shadow-sm space-y-4 animate-in fade-in duration-300">
              <div className="flex items-center gap-2 text-success font-bold text-sm">
                <CheckCircle className="w-5 h-5" />
                <span>Order Verified &amp; Confirmed!</span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-border">
                  <span className="text-text-secondary">Order ID:</span>
                  <span className="font-mono font-bold text-text-primary">{confirmedOrder.id}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border">
                  <span className="text-text-secondary">Payment State:</span>
                  <Badge variant="success">PAID</Badge>
                </div>
                <div className="flex justify-between py-1 border-b border-border">
                  <span className="text-text-secondary">Fulfillment Status:</span>
                  <Badge variant="accent">{confirmedOrder.status || "CONFIRMED"}</Badge>
                </div>
                <div className="flex justify-between py-1 border-b border-border">
                  <span className="text-text-secondary">Tracking Number:</span>
                  <span className="font-mono text-text-primary">{confirmedOrder.tracking_number || "BLR-98421"}</span>
                </div>
              </div>

              <div className="pt-2">
                <Link to={`/orders/${confirmedOrder.id}`} target="_blank">
                  <Button variant="outline" size="sm" className="w-full text-xs" icon={<ExternalLink className="w-3.5 h-3.5" />}>
                    View in Customer Storefront
                  </Button>
                </Link>
              </div>
            </div>
          )}

          {/* Interactive Tool Explorer Collapsible (Internal Debug/Test Helper) */}
          <div className="bg-surface rounded-2xl border border-border p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-accent" />
                <div>
                  <h3 className="text-sm font-bold text-text-primary">MCP Tool Debug Explorer</h3>
                  <p className="text-[10px] text-text-muted">Internal testing helper via /api/mcp/execute</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="text-[11px] h-7 px-2"
                onClick={() => setShowToolsRegistry(!showToolsRegistry)}
              >
                {showToolsRegistry ? "Hide Tools" : loadingTools ? "Loading Tools..." : `Inspect (${tools.length})`}
              </Button>
            </div>

            {showToolsRegistry && (
              <div className="space-y-3 pt-1 text-xs">
                <div>
                  <label className="text-[11px] font-medium text-text-secondary">Select Tool to Test:</label>
                  <select
                    className="w-full mt-1 p-2 rounded-lg border border-border bg-surface text-text-primary font-mono text-xs focus:ring-1 focus:ring-accent"
                    value={selectedToolToTest}
                    onChange={(e) => setSelectedToolToTest(e.target.value)}
                  >
                    {tools.map((t) => (
                      <option key={t.name} value={t.name}>
                        {t.name}()
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-medium text-text-secondary">Arguments (JSON):</label>
                  <textarea
                    rows={3}
                    className="w-full mt-1 p-2 rounded-lg border border-border bg-surface text-text-primary font-mono text-[11px] focus:ring-1 focus:ring-accent"
                    value={customToolArgs}
                    onChange={(e) => setCustomToolArgs(e.target.value)}
                    placeholder="{}"
                  />
                </div>

                <Button
                  variant="secondary"
                  size="sm"
                  className="w-full text-xs"
                  onClick={handleTestSingleTool}
                  disabled={testingTool}
                  icon={testingTool ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                >
                  {testingTool ? "Calling Tool..." : `Execute ${selectedToolToTest}()`}
                </Button>

                {toolTestResult && (
                  <div className="p-3 rounded-lg bg-surface-secondary border border-border max-h-40 overflow-y-auto text-[10px] font-mono">
                    <pre>{JSON.stringify(toolTestResult, null, 2)}</pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExternalBuyerPage;
