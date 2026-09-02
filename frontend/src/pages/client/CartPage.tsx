import React from "react";
import CartSummary from "../../components/checkout/CartSummary";

export const CartPage: React.FC = () => {
  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary">Your Shopping Cart</h1>
        <p className="text-xs sm:text-sm text-text-secondary mt-1">
          Authoritative pricing and inventory reserved live in our warehouse system.
        </p>
      </div>

      <CartSummary />
    </div>
  );
};

export default CartPage;
