import React from "react";
import { Bot, User } from "lucide-react";
import type { Product, Quote } from "../../types/domain";
import ToolActivity from "./ToolActivity";
import ProductRecommendation from "./ProductRecommendation";
import ApprovalCard from "./ApprovalCard";

export interface MessageData {
  id: string;
  sender: "user" | "assistant";
  content: string;
  toolActivity?: { activity: string; status: "running" | "completed" | "failed"; details?: string }[];
  recommendations?: { product: Product; reason?: string }[];
  approvalQuote?: Quote;
  timestamp: string;
}

export interface ChatMessageProps {
  message: MessageData;
  onApproveQuote?: () => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onApproveQuote }) => {
  const isUser = message.sender === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"} items-start my-3`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-2xs ${
          isUser
            ? "bg-text-dark text-surface"
            : "bg-accent text-accent-foreground"
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4.5 h-4.5" />}
      </div>

      {/* Bubble & Rich Contents */}
      <div className={`max-w-[85%] space-y-2.5 ${isUser ? "items-end text-right" : "items-start text-left"}`}>
        {/* Text Message */}
        <div
          className={`inline-block px-4 py-2.5 rounded-2xl text-xs sm:text-sm leading-relaxed ${
            isUser
              ? "bg-accent text-accent-foreground rounded-tr-xs"
              : "bg-surface-secondary text-text-primary border border-border rounded-tl-xs"
          }`}
        >
          {message.content}
        </div>

        {/* Tool Activity Statuses */}
        {message.toolActivity && message.toolActivity.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-0.5">
            {message.toolActivity.map((tool, idx) => (
              <ToolActivity
                key={idx}
                activity={tool.activity}
                status={tool.status}
                details={tool.details}
              />
            ))}
          </div>
        )}

        {/* Product Recommendations */}
        {message.recommendations && message.recommendations.length > 0 && (
          <div className="space-y-2 pt-1 w-full">
            {message.recommendations.map((rec) => (
              <ProductRecommendation
                key={rec.product.id}
                product={rec.product}
                reason={rec.reason}
              />
            ))}
          </div>
        )}

        {/* Authoritative Approval Card */}
        {message.approvalQuote && (
          <div className="pt-1 w-full">
            <ApprovalCard quote={message.approvalQuote} onApprove={onApproveQuote} />
          </div>
        )}

        {/* Timestamp */}
        <span className="block text-[10px] text-text-muted px-1">
          {message.timestamp}
        </span>
      </div>
    </div>
  );
};

export default ChatMessage;
