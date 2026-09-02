/**
 * Shared Domain Types for Agentic Commerce
 * Strictly typed definitions matching backend SQLAlchemy models and API contracts.
 */

export type ApiError = {
  code: string;
  message: string;
};

export type ApiResponse<T> = {
  success: boolean;
  data?: T;
  error?: ApiError;
};

export type HealthStatus = {
  status: string;
  service: string;
  version: string;
};

export type Product = {
  id: string;
  merchant_id: string;
  sku: string;
  name: string;
  category: string;
  short_description: string;
  description: string;
  price_paise: number;
  inventory_quantity: number;
  image_url: string;
  tags: string[];
  attributes: Record<string, unknown>;
  active: boolean;
  created_at: string;
  updated_at: string;
};

export type Merchant = {
  id: string;
  name: string;
  slug: string;
  created_at: string;
};

export type AdminUser = {
  id: string;
  merchant_id: string;
  email: string;
  role: string;
  created_at?: string;
};

export type AdminLoginResponse = {
  token: string;
  admin: AdminUser;
};

export type CrossSellRule = {
  trigger_category: string;
  recommend_category: string;
  reason: string;
};

export type DeliveryRules = {
  free_delivery_threshold_paise: number;
  standard_delivery_paise: number;
  express_delivery_paise: number;
  estimated_days_standard: number;
  estimated_days_express: number;
};

export type MerchantPolicy = {
  id: string;
  merchant_id: string;
  max_discount_percent: number;
  allow_out_of_stock: boolean;
  require_purchase_approval: boolean;
  cross_sell_rules: CrossSellRule[];
  delivery_rules: DeliveryRules;
  updated_at: string;
};

export type CartItem = {
  id: string;
  cart_id: string;
  product_id: string;
  quantity: number;
  unit_price_paise_snapshot: number;
  product?: Product;
  created_at: string;
  updated_at: string;
};

export type Cart = {
  id: string;
  merchant_id: string;
  session_id: string;
  status: "active" | "converted" | "abandoned";
  currency: string;
  items: CartItem[];
  created_at: string;
  updated_at: string;
};

export type QuoteItem = {
  product_id: string;
  sku: string;
  name: string;
  quantity: number;
  unit_price_paise: number;
  total_paise: number;
  in_stock: boolean;
};

export type Quote = {
  cart_id: string;
  items: QuoteItem[];
  subtotal_paise: number;
  discount_paise: number;
  delivery_paise: number;
  total_paise: number;
  currency: string;
  valid: boolean;
  warnings: string[];
};

export type ShippingAddress = {
  line1: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
};

export type OrderStatus =
  | "PENDING_PAYMENT"
  | "PAID"
  | "CONFIRMED"
  | "FULFILLED"
  | "CANCELLED";

export type OrderItemSnapshot = {
  product_id: string;
  sku: string;
  name: string;
  quantity: number;
  unit_price_paise: number;
  total_paise: number;
};

export type Order = {
  id: string;
  merchant_id: string;
  cart_id?: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  shipping_address: ShippingAddress;
  items?: OrderItemSnapshot[];
  amount_paise: number;
  currency: string;
  status: OrderStatus;
  razorpay_order_id?: string;
  approved_at?: string;
  paid_at?: string;
  confirmed_at?: string;
  created_at: string;
  updated_at: string;
};

export type CheckoutInitiateRequest = {
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  shipping_address: ShippingAddress;
  approved_total_paise: number;
};

export type CheckoutInitiateResponse = {
  merchant_order_id: string;
  razorpay_order_id: string;
  razorpay_key_id: string;
  amount_paise: number;
  currency: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
};

export type PaymentVerifyRequest = {
  merchant_order_id: string;
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
};

export type PaymentVerifyResponse = {
  order_id: string;
  status: OrderStatus;
  amount_paise: number;
  currency: string;
  paid_at?: string;
  confirmed_at?: string;
};

export type PaymentAttempt = {
  id: string;
  merchant_order_id: string;
  razorpay_order_id: string;
  razorpay_payment_id?: string;
  status: string;
  signature_verified: boolean;
  raw_event_reference?: string;
  created_at: string;
};

export type AuditEvent = {
  id: string;
  merchant_id?: string;
  session_id?: string;
  actor_type: "shopper" | "in_app_agent" | "external_ai" | "admin" | "system";
  action: string;
  entity_type: string;
  entity_id?: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type ProductAvailability = {
  product_id: string;
  sku: string;
  name: string;
  price_paise: number;
  inventory_quantity: number;
  in_stock: boolean;
  active: boolean;
};

export type DeliveryEstimate = {
  standard_delivery_paise: number;
  express_delivery_paise: number;
  free_delivery_threshold_paise: number;
  estimated_days_standard: number;
  estimated_days_express: number;
  delivery_paise: number;
  is_free: boolean;
};

export type OfferItem = {
  id: string;
  title: string;
  description: string;
  discount_percent?: number;
  terms?: string;
};

export type OffersResponse = {
  offers: OfferItem[];
  max_discount_percent: number;
};

export type ChatMessageTurn = {
  role: "user" | "assistant";
  content: string;
};

export type ToolActivityItem = {
  activity: string;
  status: "running" | "completed" | "failed";
  details?: string;
};

export type ProductRecommendationItem = {
  product: Product;
  reason?: string;
};

export type AgentChatRequest = {
  message: string;
  session_id: string;
  cart_id?: string;
  history?: ChatMessageTurn[];
};

export type AgentChatResponse = {
  message: string;
  tool_activity: ToolActivityItem[];
  recommendations: ProductRecommendationItem[];
  cart?: Cart;
  quote?: Quote;
  approval_required: boolean;
};

