import React, { createContext, useContext, useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { Product, CartItem, MerchantPolicy, Order, Quote } from "../../types/domain";
import { MOCK_PRODUCTS, MOCK_POLICY, MOCK_ORDERS, MOCK_MERCHANT } from "./mockData";
import { apiClient } from "../api/client";

export interface MockCommerceContextType {
  // Products
  products: Product[];
  addProduct: (product: Omit<Product, "id" | "merchant_id" | "created_at" | "updated_at">) => Product;
  updateProduct: (id: string, updates: Partial<Product>) => void;
  deleteProduct: (id: string) => void;
  getProduct: (id: string) => Product | undefined;

  // Cart (Authoritative Backend)
  cartId?: string;
  cartItems: CartItem[];
  addToCart: (product: Product, quantity?: number) => void;
  removeFromCart: (productIdOrItemId: string) => void;
  updateQuantity: (productIdOrItemId: string, quantity: number) => void;
  clearCart: () => void;
  cartCount: number;
  cartSubtotalPaise: number;
  isCartLoading: boolean;

  // Drawers
  isCartOpen: boolean;
  setIsCartOpen: (open: boolean) => void;
  isAssistantOpen: boolean;
  setIsAssistantOpen: (open: boolean) => void;

  // Policy
  policy: MerchantPolicy;
  updatePolicy: (updates: Partial<MerchantPolicy>) => void;

  // Orders (Mock for future phases)
  orders: Order[];
  createOrder: (data: Omit<Order, "id" | "merchant_id" | "created_at" | "updated_at">) => Order;
  getOrder: (id: string) => Order | undefined;

  // Active Quote (Authoritative Backend)
  activeQuote: Quote;
}

const MockCommerceContext = createContext<MockCommerceContextType | null>(null);

export const MockCommerceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = useQueryClient();

  const [products, setProducts] = useState<Product[]>(MOCK_PRODUCTS);
  const [orders, setOrders] = useState<Order[]>(MOCK_ORDERS);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);

  // 1. Authoritative Backend Cart (Idempotent Get-or-Create)
  const { data: cartResponse, isLoading: isCartLoading } = useQuery({
    queryKey: ["active-cart"],
    queryFn: async () => {
      try {
        return await apiClient.getOrCreateCart();
      } catch (err) {
        console.warn("Failed to retrieve backend cart; using empty fallback", err);
        return null;
      }
    },
  });

  const cart = cartResponse?.data;
  const cartItems: CartItem[] = useMemo(() => cart?.items || [], [cart?.items]);

  // 2. Authoritative Backend Policy
  const { data: policyResponse } = useQuery({
    queryKey: ["merchant-policy"],
    queryFn: async () => {
      try {
        return await apiClient.getAdminPolicies();
      } catch {
        return null;
      }
    },
  });

  const policy: MerchantPolicy = useMemo(() => {
    return policyResponse?.data || MOCK_POLICY;
  }, [policyResponse?.data]);

  // 3. Authoritative Backend Quote Calculation
  const { data: quoteResponse } = useQuery({
    queryKey: ["active-quote", cart?.id, cartItems],
    queryFn: async () => {
      if (!cart?.id) return null;
      try {
        return await apiClient.getCartQuote(cart.id);
      } catch (err) {
        console.warn("Failed to calculate server quote", err);
        return null;
      }
    },
    enabled: !!cart?.id,
  });

  const activeQuote: Quote = useMemo(() => {
    if (quoteResponse?.data) {
      return quoteResponse.data;
    }
    const subtotal = cartItems.reduce(
      (acc, item) => acc + (item.product?.price_paise ?? item.unit_price_paise_snapshot) * item.quantity,
      0
    );
    const deliveryThreshold = policy.delivery_rules?.free_delivery_threshold_paise ?? 100000;
    const deliveryFee = subtotal >= deliveryThreshold || subtotal === 0 ? 0 : (policy.delivery_rules?.standard_delivery_paise ?? 15000);
    return {
      cart_id: cart?.id || "",
      items: cartItems.map((item) => ({
        product_id: item.product_id,
        sku: item.product?.sku || item.product_id,
        name: item.product?.name || "Product",
        quantity: item.quantity,
        unit_price_paise: item.product?.price_paise ?? item.unit_price_paise_snapshot,
        total_paise: (item.product?.price_paise ?? item.unit_price_paise_snapshot) * item.quantity,
        in_stock: item.product ? item.product.inventory_quantity >= item.quantity : true,
      })),
      subtotal_paise: subtotal,
      discount_paise: 0,
      delivery_paise: deliveryFee,
      total_paise: subtotal + deliveryFee,
      currency: "INR",
      valid: cartItems.length > 0,
      warnings: [],
    };
  }, [quoteResponse?.data, cart?.id, cartItems, policy]);

  // Mutations
  const addMutation = useMutation({
    mutationFn: async ({ productId, quantity }: { productId: string; quantity: number }) => {
      let targetCartId = cart?.id;
      if (!targetCartId) {
        const created = await apiClient.getOrCreateCart();
        targetCartId = created.data?.id;
      }
      if (!targetCartId) throw new Error("Could not initialize cart");
      return apiClient.addToCart(targetCartId, productId, quantity);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["active-cart"] });
      queryClient.invalidateQueries({ queryKey: ["active-quote"] });
    },
  });

  const updateQuantityMutation = useMutation({
    mutationFn: async ({ itemId, quantity }: { itemId: string; quantity: number }) => {
      if (!cart?.id) return;
      return apiClient.updateCartItemQuantity(cart.id, itemId, quantity);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["active-cart"] });
      queryClient.invalidateQueries({ queryKey: ["active-quote"] });
    },
  });

  const removeMutation = useMutation({
    mutationFn: async ({ itemId }: { itemId: string }) => {
      if (!cart?.id) return;
      return apiClient.removeCartItem(cart.id, itemId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["active-cart"] });
      queryClient.invalidateQueries({ queryKey: ["active-quote"] });
    },
  });

  const addToCart = (product: Product, quantity: number = 1) => {
    addMutation.mutate({ productId: product.id, quantity });
    setIsCartOpen(true);
  };

  const removeFromCart = (productIdOrItemId: string) => {
    const item = cartItems.find((ci) => ci.id === productIdOrItemId || ci.product_id === productIdOrItemId);
    if (!item) return;
    removeMutation.mutate({ itemId: item.id });
  };

  const updateQuantity = (productIdOrItemId: string, quantity: number) => {
    const item = cartItems.find((ci) => ci.id === productIdOrItemId || ci.product_id === productIdOrItemId);
    if (!item) return;
    updateQuantityMutation.mutate({ itemId: item.id, quantity });
  };

  const clearCart = async () => {
    if (!cart?.id || cartItems.length === 0) return;
    await Promise.all(cartItems.map((item) => apiClient.removeCartItem(cart.id, item.id)));
    queryClient.invalidateQueries({ queryKey: ["active-cart"] });
    queryClient.invalidateQueries({ queryKey: ["active-quote"] });
  };

  const cartCount = useMemo(() => {
    return cartItems.reduce((acc, item) => acc + item.quantity, 0);
  }, [cartItems]);

  const cartSubtotalPaise = useMemo(() => {
    return activeQuote.subtotal_paise || cartItems.reduce((acc, item) => {
      const price = item.product ? item.product.price_paise : item.unit_price_paise_snapshot;
      return acc + price * item.quantity;
    }, 0);
  }, [activeQuote.subtotal_paise, cartItems]);

  // Product actions (for mock fallback admin)
  const addProduct = (
    productData: Omit<Product, "id" | "merchant_id" | "created_at" | "updated_at">
  ): Product => {
    const newProduct: Product = {
      ...productData,
      id: `prod_${Date.now()}`,
      merchant_id: MOCK_MERCHANT.id,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    setProducts((prev) => [newProduct, ...prev]);
    return newProduct;
  };

  const updateProduct = (id: string, updates: Partial<Product>) => {
    setProducts((prev) =>
      prev.map((p) => (p.id === id ? { ...p, ...updates, updated_at: new Date().toISOString() } : p))
    );
  };

  const deleteProduct = (id: string) => {
    setProducts((prev) => prev.filter((p) => p.id !== id));
  };

  const getProduct = (id: string) => {
    return products.find((p) => p.id === id);
  };

  const updatePolicy = (updates: Partial<MerchantPolicy>) => {
    apiClient.updateAdminPolicies(updates).then(() => {
      queryClient.invalidateQueries({ queryKey: ["merchant-policy"] });
      queryClient.invalidateQueries({ queryKey: ["active-quote"] });
    }).catch((e) => console.warn("Failed to update policy on server", e));
  };

  // Orders (Mock for future phases)
  const createOrder = (
    data: Omit<Order, "id" | "merchant_id" | "created_at" | "updated_at">
  ): Order => {
    const newOrder: Order = {
      ...data,
      id: `ord_${Date.now()}`,
      merchant_id: MOCK_MERCHANT.id,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    setOrders((prev) => [newOrder, ...prev]);
    return newOrder;
  };

  const getOrder = (id: string) => {
    return orders.find((o) => o.id === id);
  };

  return (
    <MockCommerceContext.Provider
      value={{
        products,
        addProduct,
        updateProduct,
        deleteProduct,
        getProduct,
        cartId: cart?.id,
        cartItems,
        addToCart,
        removeFromCart,
        updateQuantity,
        clearCart,
        cartCount,
        cartSubtotalPaise,
        isCartLoading,
        isCartOpen,
        setIsCartOpen,
        isAssistantOpen,
        setIsAssistantOpen,
        policy,
        updatePolicy,
        orders,
        createOrder,
        getOrder,
        activeQuote,
      }}
    >
      {children}
    </MockCommerceContext.Provider>
  );
};

export const useMockCommerce = () => {
  const context = useContext(MockCommerceContext);
  if (!context) {
    throw new Error("useMockCommerce must be used within a MockCommerceProvider");
  }
  return context;
};
