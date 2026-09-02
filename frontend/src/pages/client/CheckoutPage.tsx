import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import CheckoutForm from "../../components/checkout/CheckoutForm";

export const CheckoutPage: React.FC = () => {
  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <Link
          to="/cart"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-text-secondary hover:text-text-primary transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Cart</span>
        </Link>
        <span className="text-xs font-semibold text-accent">Step 2 of 2: Authoritative Review</span>
      </div>

      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary">Checkout & Order Review</h1>
        <p className="text-xs sm:text-sm text-text-secondary mt-1">
          Review customer contact, delivery address, and authoritative pricing before providing purchase approval.
        </p>
      </div>

      <CheckoutForm />
    </div>
  );
};

export default CheckoutPage;
