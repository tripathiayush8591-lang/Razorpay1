import React from "react";
import { Link } from "react-router-dom";
import { X, HelpCircle, Package, Bot, Mail, Phone, Clock } from "lucide-react";
import { Button } from "../ui/Button";

export interface SupportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenAssistant?: () => void;
}

export const SupportModal: React.FC<SupportModalProps> = ({
  isOpen,
  onClose,
  onOpenAssistant,
}) => {
  if (!isOpen) return null;

  const faqs = [
    {
      q: "How fast is shipping?",
      a: "Orders are dispatched within 24 hours. Delivery takes 2–4 business days across India. Orders over ₹5,000 get free express shipping.",
    },
    {
      q: "When am I charged for my order?",
      a: "You are only charged after you inspect your complete item breakdown and approve payment in the secure Razorpay checkout window.",
    },
    {
      q: "Can I track my shipment live?",
      a: "Yes! Use 'Track Orders' in the header or ask Pace 'Where is my order?' to see real-time courier updates and tracking numbers.",
    },
    {
      q: "Can I exchange shoe sizes?",
      a: "We offer 30-day exchanges for unworn shoes in their original packaging.",
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="bg-surface rounded-2xl border border-border max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in zoom-in-95 duration-200 overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-labelledby="support-modal-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-accent-light flex items-center justify-center text-accent-dark">
              <HelpCircle className="w-4 h-4" />
            </div>
            <div>
              <h2 id="support-modal-title" className="text-sm font-bold text-text-primary">
                RunCraft Support & Help
              </h2>
              <p className="text-[11px] text-text-secondary">Here to keep you moving</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-secondary transition cursor-pointer"
            aria-label="Close support modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Quick Help Actions */}
        <div className="grid grid-cols-2 gap-3">
          <Link
            to="/orders"
            onClick={onClose}
            className="p-3 rounded-xl bg-surface-secondary border border-border hover:border-accent/40 transition flex items-center gap-2.5 group"
          >
            <div className="w-8 h-8 rounded-lg bg-surface flex items-center justify-center text-accent shrink-0 shadow-2xs">
              <Package className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <span className="text-xs font-bold text-text-primary block truncate group-hover:text-accent transition">
                Track Orders
              </span>
              <span className="text-[10px] text-text-secondary truncate block">Courier updates</span>
            </div>
          </Link>

          <button
            onClick={() => {
              onClose();
              if (onOpenAssistant) onOpenAssistant();
            }}
            className="p-3 rounded-xl bg-surface-secondary border border-border hover:border-accent/40 transition flex items-center gap-2.5 text-left group cursor-pointer"
          >
            <div className="w-8 h-8 rounded-lg bg-surface flex items-center justify-center text-accent shrink-0 shadow-2xs">
              <Bot className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <span className="text-xs font-bold text-text-primary block truncate group-hover:text-accent transition">
                Ask Pace (AI)
              </span>
              <span className="text-[10px] text-text-secondary truncate block">Instant answers</span>
            </div>
          </button>
        </div>

        {/* FAQ Accordion / List */}
        <div className="space-y-2.5">
          <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
            Frequently Asked Questions
          </h3>
          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {faqs.map((faq, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded-xl bg-surface-secondary/60 border border-border text-xs space-y-0.5"
              >
                <p className="font-semibold text-text-primary">{faq.q}</p>
                <p className="text-[11px] text-text-secondary leading-relaxed">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Contact info */}
        <div className="pt-3 border-t border-border flex flex-col sm:flex-row items-start sm:items-center justify-between text-xs text-text-secondary gap-2">
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1 text-[11px]">
              <Mail className="w-3.5 h-3.5 text-text-muted" /> support@runcraft.internal
            </span>
            <span className="inline-flex items-center gap-1 text-[11px]">
              <Phone className="w-3.5 h-3.5 text-text-muted" /> +91 80 4765 3000
            </span>
          </div>
          <span className="inline-flex items-center gap-1 text-[10px] text-text-muted">
            <Clock className="w-3 h-3" /> Mon–Sat 9am–8pm IST
          </span>
        </div>

        {/* Close Button */}
        <Button variant="outline" size="sm" onClick={onClose} className="w-full justify-center">
          Close Help
        </Button>
      </div>
    </div>
  );
};

export default SupportModal;
