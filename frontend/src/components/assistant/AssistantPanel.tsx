import React, { useState, useRef, useEffect } from "react";
import { Send, Sparkles, RefreshCw, X, Maximize2 } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import ChatMessage, { MessageData } from "./ChatMessage";
import { apiClient } from "../../lib/api/client";
import { getOrCreateGuestSessionId } from "../../lib/session";

export interface AssistantPanelProps {
  isFullPage?: boolean;
  onClose?: () => void;
}

export const AssistantPanel: React.FC<AssistantPanelProps> = ({
  isFullPage = false,
  onClose,
}) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Authoritative active cart query
  const { data: cartData } = useQuery({
    queryKey: ["cart"],
    queryFn: () => apiClient.getOrCreateCart(),
  });

  const cart = cartData?.data;

  const [messages, setMessages] = useState<MessageData[]>([
    {
      id: "msg_welcome",
      sender: "assistant",
      content:
        "Hello! I am your RunCraft AI Commerce Assistant. I can search our live catalog, verify real inventory, assemble gear kits, and prepare an authoritative quote for you.",
      timestamp: "Just now",
    },
  ]);

  const [inputValue, setInputValue] = useState("");

  const quickPrompts = [
    "Build a beginner running kit under ₹8,000",
    "Find race day carbon plate shoes",
    "Add hydration flask",
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Real backend agent chat mutation
  const chatMutation = useMutation({
    mutationFn: async (textToSend: string) => {
      const activeCart = cart || (await apiClient.getOrCreateCart()).data;
      if (!activeCart) throw new Error("Cart unavailable");
      const history = messages
        .filter((m) => m.id !== "msg_welcome")
        .slice(-6)
        .map((m) => ({
          role: m.sender as "user" | "assistant",
          content: m.content,
        }));

      const res = await apiClient.agentChat({
        message: textToSend,
        session_id: getOrCreateGuestSessionId(),
        cart_id: activeCart.id,
        history,
      });
      if (!res.data) throw new Error("No response data received from agent");
      return res.data;
    },
    onSuccess: (data) => {
      // Sync authoritative cart state across storefront immediately
      if (data.cart) {
        queryClient.setQueryData(["cart"], { success: true, data: data.cart });
      }
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      queryClient.invalidateQueries({ queryKey: ["quote"] });

      const assistantMsg: MessageData = {
        id: `msg_asst_${Date.now()}`,
        sender: "assistant",
        content: data.message,
        toolActivity: data.tool_activity,
        recommendations: data.recommendations,
        approvalQuote: data.quote || undefined,
        timestamp: "Just now",
      };

      setMessages((prev) => [...prev, assistantMsg]);
    },
    onError: (err: any) => {
      const errMsg: MessageData = {
        id: `msg_err_${Date.now()}`,
        sender: "assistant",
        content:
          err?.message ||
          "I encountered an unexpected issue while consulting the commerce services. Please try again.",
        timestamp: "Just now",
      };
      setMessages((prev) => [...prev, errMsg]);
    },
  });

  const handleSend = (textToSend?: string) => {
    const text = textToSend || inputValue;
    if (!text.trim() || chatMutation.isPending) return;

    const userMsg: MessageData = {
      id: `msg_user_${Date.now()}`,
      sender: "user",
      content: text,
      timestamp: "Just now",
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    chatMutation.mutate(text);
  };

  const handleApproveQuote = () => {
    if (onClose) onClose();
    navigate("/checkout");
  };

  return (
    <div
      className={`flex flex-col bg-surface border border-border overflow-hidden ${
        isFullPage
          ? "h-[calc(100vh-140px)] rounded-2xl shadow-sm"
          : "h-[560px] w-[380px] sm:w-[420px] rounded-2xl shadow-2xl"
      }`}
    >
      {/* Header */}
      <div className="px-4 py-3.5 border-b border-border bg-surface-secondary/70 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-accent flex items-center justify-center text-accent-foreground shadow-2xs">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-text-primary flex items-center gap-1.5">
              RunCraft AI Assistant
              <span className="w-2 h-2 rounded-full bg-success inline-block animate-pulse" />
            </h3>
            <p className="text-[10px] text-text-secondary">Authoritative Commerce Agent</p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          {!isFullPage && (
            <Link
              to="/assistant"
              onClick={onClose}
              className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-secondary transition"
              title="Open full page"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </Link>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-secondary transition cursor-pointer"
              aria-label="Close assistant"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2 text-xs">
        {messages.map((msg) => (
          <ChatMessage
            key={msg.id}
            message={msg}
            onApproveQuote={handleApproveQuote}
          />
        ))}

        {chatMutation.isPending && (
          <div className="flex items-center gap-2 text-text-secondary text-xs p-3 bg-surface-secondary/50 rounded-xl border border-border">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-accent" />
            <span>Consulting live catalog & inventory services...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick suggestions pills */}
      <div className="px-4 py-2 border-t border-border bg-surface-secondary/30 flex gap-1.5 overflow-x-auto no-scrollbar">
        {quickPrompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(prompt)}
            disabled={chatMutation.isPending}
            className="text-[11px] whitespace-nowrap px-2.5 py-1 rounded-full bg-surface border border-border text-text-secondary hover:text-text-primary hover:border-accent/40 transition cursor-pointer shrink-0 disabled:opacity-50"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input bar */}
      <div className="p-3 border-t border-border bg-surface flex items-center gap-2">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask for running shoes, beginner kits, or advice..."
          disabled={chatMutation.isPending}
          className="flex-1 bg-surface-secondary text-text-primary text-xs rounded-xl px-3 py-2.5 border border-border focus:outline-hidden focus:border-accent focus:ring-1 focus:ring-accent placeholder:text-text-muted"
        />
        <button
          onClick={() => handleSend()}
          disabled={!inputValue.trim() || chatMutation.isPending}
          className="p-2.5 rounded-xl bg-accent text-accent-foreground hover:bg-accent-dark transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shadow-xs"
          aria-label="Send message"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};

export default AssistantPanel;
