import type {
  ApiResponse,
  HealthStatus,
  Product,
  AdminUser,
  AdminLoginResponse,
  MerchantPolicy,
  Cart,
  Quote,
  ProductAvailability,
  DeliveryEstimate,
  OffersResponse,
  AgentChatRequest,
  AgentChatResponse,
  CheckoutInitiateRequest,
  CheckoutInitiateResponse,
  PaymentVerifyRequest,
  PaymentVerifyResponse,
  Order,
  AdminOrdersPageResponse,
  FulfillmentUpdateRequest,
  AuditEvent,
  MCPToolSchemaInfo,
  ExternalBuyerChatRequest,
  ExternalBuyerChatResponse,
} from "@/types/domain";
import { getOrCreateGuestSessionId } from "@/lib/session";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export class ApiErrorClass extends Error {
  code: string;
  constructor(message: string, code: string = "UNKNOWN_ERROR") {
    super(message);
    this.name = "ApiErrorClass";
    this.code = code;
  }
}

/**
 * Resolves static relative image URLs (/static/uploads/...) to absolute URLs if API_BASE_URL is set,
 * or returns them as-is if proxied or already an absolute URL.
 */
export function resolveImageUrl(url?: string): string {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://") || url.startsWith("data:")) {
    return url;
  }
  if (url.startsWith("/")) {
    return `${API_BASE_URL}${url}`;
  }
  return url;
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  // Read admin token from sessionStorage if present
  const adminToken = typeof window !== "undefined" ? sessionStorage.getItem("admin_token") : null;
  const guestSessionId = getOrCreateGuestSessionId();

  const headers: Record<string, string> = {
    ...(options?.headers as Record<string, string>),
  };

  // Only set Content-Type if not sending FormData
  if (!(options?.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  if (adminToken && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${adminToken}`;
  }

  if (guestSessionId && !headers["X-Session-ID"]) {
    headers["X-Session-ID"] = guestSessionId;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.error?.message) {
        throw new ApiErrorClass(errJson.error.message, errJson.error.code || "API_ERROR");
      }
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch (e) {
      if (e instanceof ApiErrorClass) throw e;
    }
    throw new ApiErrorClass(errorDetail, `HTTP_${response.status}`);
  }

  return response.json();
}

export const apiClient = {
  get: <T>(endpoint: string) => request<T>(endpoint, { method: "GET" }),
  post: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, {
      method: "POST",
      body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),
  put: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),
  delete: <T>(endpoint: string) => request<T>(endpoint, { method: "DELETE" }),

  // Health
  async checkHealth(): Promise<HealthStatus> {
    return request<HealthStatus>("/api/health");
  },

  // Public Storefront Catalog
  async getProducts(params?: {
    q?: string;
    category?: string;
    max_price_paise?: number;
  }): Promise<ApiResponse<Product[]>> {
    const query = new URLSearchParams();
    if (params?.q) query.set("q", params.q);
    if (params?.category && params.category !== "all") query.set("category", params.category);
    if (params?.max_price_paise) query.set("max_price_paise", params.max_price_paise.toString());

    const queryString = query.toString() ? `?${query.toString()}` : "";
    return request<ApiResponse<Product[]>>(`/api/products${queryString}`);
  },

  async getProductById(id: string): Promise<ApiResponse<Product>> {
    return request<ApiResponse<Product>>(`/api/products/${id}`);
  },

  // Admin Auth
  async adminLogin(email: string, password: string): Promise<ApiResponse<AdminLoginResponse>> {
    return request<ApiResponse<AdminLoginResponse>>("/api/admin/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  async getAdminMe(): Promise<ApiResponse<AdminUser>> {
    return request<ApiResponse<AdminUser>>("/api/admin/me");
  },

  // Admin Catalog CRUD
  async getAdminProducts(params?: {
    q?: string;
    category?: string;
    max_price_paise?: number;
    active_only?: boolean;
  }): Promise<ApiResponse<Product[]>> {
    const query = new URLSearchParams();
    if (params?.q) query.set("q", params.q);
    if (params?.category && params.category !== "all") query.set("category", params.category);
    if (params?.max_price_paise) query.set("max_price_paise", params.max_price_paise.toString());
    if (params?.active_only !== undefined) query.set("active_only", params.active_only.toString());

    const queryString = query.toString() ? `?${query.toString()}` : "";
    return request<ApiResponse<Product[]>>(`/api/admin/products${queryString}`);
  },

  async getAdminProductById(id: string): Promise<ApiResponse<Product>> {
    return request<ApiResponse<Product>>(`/api/admin/products/${id}`);
  },

  async createAdminProduct(
    product: Omit<Product, "id" | "merchant_id" | "created_at" | "updated_at">
  ): Promise<ApiResponse<Product>> {
    return request<ApiResponse<Product>>("/api/admin/products", {
      method: "POST",
      body: JSON.stringify(product),
    });
  },

  async updateAdminProduct(
    id: string,
    updates: Partial<Product>
  ): Promise<ApiResponse<Product>> {
    return request<ApiResponse<Product>>(`/api/admin/products/${id}`, {
      method: "PATCH",
      body: JSON.stringify(updates),
    });
  },

  async deleteAdminProduct(id: string): Promise<ApiResponse<Product>> {
    return request<ApiResponse<Product>>(`/api/admin/products/${id}`, {
      method: "DELETE",
    });
  },

  // Multipart Image Upload to local FastAPI static directory
  async uploadProductImage(file: File): Promise<ApiResponse<{ url: string; filename: string; size_bytes: number }>> {
    const formData = new FormData();
    formData.append("file", file);
    return request<ApiResponse<{ url: string; filename: string; size_bytes: number }>>(
      "/api/admin/upload",
      {
        method: "POST",
        body: formData,
      }
    );
  },

  // Admin Policies
  async getAdminPolicies(): Promise<ApiResponse<MerchantPolicy>> {
    return request<ApiResponse<MerchantPolicy>>("/api/admin/policies");
  },

  async updateAdminPolicies(
    updates: Partial<MerchantPolicy>
  ): Promise<ApiResponse<MerchantPolicy>> {
    return request<ApiResponse<MerchantPolicy>>("/api/admin/policies", {
      method: "PUT",
      body: JSON.stringify(updates),
    });
  },

  // Authoritative Cart Management
  async getOrCreateCart(sessionId?: string): Promise<ApiResponse<Cart>> {
    const session = sessionId || getOrCreateGuestSessionId();
    return request<ApiResponse<Cart>>("/api/carts", {
      method: "POST",
      body: JSON.stringify({ session_id: session }),
    });
  },

  async getCart(cartId: string): Promise<ApiResponse<Cart>> {
    return request<ApiResponse<Cart>>(`/api/carts/${cartId}`);
  },

  async addToCart(cartId: string, productId: string, quantity: number = 1): Promise<ApiResponse<Cart>> {
    return request<ApiResponse<Cart>>(`/api/carts/${cartId}/items`, {
      method: "POST",
      body: JSON.stringify({ product_id: productId, quantity }),
    });
  },

  async updateCartItemQuantity(cartId: string, itemId: string, quantity: number): Promise<ApiResponse<Cart>> {
    return request<ApiResponse<Cart>>(`/api/carts/${cartId}/items/${itemId}`, {
      method: "PATCH",
      body: JSON.stringify({ quantity }),
    });
  },

  async removeCartItem(cartId: string, itemId: string): Promise<ApiResponse<Cart>> {
    return request<ApiResponse<Cart>>(`/api/carts/${cartId}/items/${itemId}`, {
      method: "DELETE",
    });
  },

  // Authoritative Quote Generation
  async getCartQuote(cartId: string): Promise<ApiResponse<Quote>> {
    return request<ApiResponse<Quote>>(`/api/carts/${cartId}/quote`, {
      method: "POST",
    });
  },

  // Product Discovery & Auxiliaries
  async getProductAvailability(productId: string): Promise<ApiResponse<ProductAvailability>> {
    return request<ApiResponse<ProductAvailability>>(`/api/products/${productId}/availability`);
  },

  async getRelatedProducts(productId: string, limit: number = 4): Promise<ApiResponse<Product[]>> {
    return request<ApiResponse<Product[]>>(`/api/products/${productId}/related?limit=${limit}`);
  },

  async getOffers(): Promise<ApiResponse<OffersResponse>> {
    return request<ApiResponse<OffersResponse>>("/api/offers");
  },

  async getDeliveryEstimate(subtotalPaise: number, postalCode?: string): Promise<ApiResponse<DeliveryEstimate>> {
    const params = new URLSearchParams();
    params.set("subtotal_paise", subtotalPaise.toString());
    if (postalCode) params.set("postal_code", postalCode);
    return request<ApiResponse<DeliveryEstimate>>(`/api/delivery/estimate?${params.toString()}`);
  },

  // In-App Commerce Agent
  async agentChat(req: AgentChatRequest): Promise<ApiResponse<AgentChatResponse>> {
    return request<ApiResponse<AgentChatResponse>>("/api/agent/chat", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  async agentToolSearchProducts(params?: {
    q?: string;
    category?: string;
    max_price_paise?: number;
  }): Promise<ApiResponse<Product[]>> {
    return request<ApiResponse<Product[]>>("/api/agent/tools/search-products", {
      method: "POST",
      body: JSON.stringify(params || {}),
    });
  },

  async agentToolGetProduct(productId: string): Promise<ApiResponse<Product>> {
    return request<ApiResponse<Product>>("/api/agent/tools/get-product", {
      method: "POST",
      body: JSON.stringify({ product_id: productId }),
    });
  },

  async agentToolAddToCart(
    cartId: string,
    productId: string,
    quantity: number = 1
  ): Promise<ApiResponse<Cart>> {
    return request<ApiResponse<Cart>>("/api/agent/tools/add-to-cart", {
      method: "POST",
      body: JSON.stringify({ cart_id: cartId, product_id: productId, quantity }),
    });
  },

  async agentToolRemoveFromCart(cartId: string, itemId: string): Promise<ApiResponse<Cart>> {
    return request<ApiResponse<Cart>>("/api/agent/tools/remove-from-cart", {
      method: "POST",
      body: JSON.stringify({ cart_id: cartId, item_id: itemId }),
    });
  },

  async agentToolGetFinalQuote(cartId: string): Promise<ApiResponse<Quote>> {
    return request<ApiResponse<Quote>>("/api/agent/tools/get-final-quote", {
      method: "POST",
      body: JSON.stringify({ cart_id: cartId }),
    });
  },

  // Authoritative Checkout & Razorpay
  async createCheckout(
    cartId: string,
    payload: CheckoutInitiateRequest
  ): Promise<ApiResponse<CheckoutInitiateResponse>> {
    return request<ApiResponse<CheckoutInitiateResponse>>(`/api/carts/${cartId}/checkout`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async verifyPayment(
    payload: PaymentVerifyRequest
  ): Promise<ApiResponse<PaymentVerifyResponse>> {
    return request<ApiResponse<PaymentVerifyResponse>>("/api/payments/razorpay/verify", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getOrder(orderId: string): Promise<ApiResponse<Order>> {
    return request<ApiResponse<Order>>(`/api/orders/${orderId}`);
  },

  async getOrders(): Promise<ApiResponse<Order[]>> {
    return request<ApiResponse<Order[]>>("/api/orders");
  },

  // Admin Order Management
  async getAdminOrders(params?: {
    q?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<ApiResponse<AdminOrdersPageResponse>> {
    const query = new URLSearchParams();
    if (params?.q) query.set("q", params.q);
    if (params?.status && params.status !== "all") query.set("status", params.status);
    if (params?.limit) query.set("limit", params.limit.toString());
    if (params?.offset) query.set("offset", params.offset.toString());

    const queryString = query.toString() ? `?${query.toString()}` : "";
    return request<ApiResponse<AdminOrdersPageResponse>>(`/api/admin/orders${queryString}`);
  },

  async getAdminOrder(orderId: string): Promise<ApiResponse<Order>> {
    return request<ApiResponse<Order>>(`/api/admin/orders/${orderId}`);
  },

  async updateAdminFulfillment(
    orderId: string,
    payload: FulfillmentUpdateRequest
  ): Promise<ApiResponse<Order>> {
    return request<ApiResponse<Order>>(`/api/admin/orders/${orderId}/fulfillment`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getAdminOrderAudit(orderId: string): Promise<ApiResponse<AuditEvent[]>> {
    return request<ApiResponse<AuditEvent[]>>(`/api/admin/orders/${orderId}/audit`);
  },

  // MCP / External AI Buyer methods
  async getMcpTools(): Promise<ApiResponse<MCPToolSchemaInfo[]>> {
    return request<ApiResponse<MCPToolSchemaInfo[]>>("/api/mcp/tools");
  },

  async executeMcpTool<T = any>(
    tool_name: string,
    argumentsPayload: Record<string, any>
  ): Promise<ApiResponse<{ tool_name: string; is_error: boolean; result: T }>> {
    return request<ApiResponse<{ tool_name: string; is_error: boolean; result: T }>>("/api/mcp/execute", {
      method: "POST",
      body: JSON.stringify({ tool_name, arguments: argumentsPayload }),
    });
  },

  async runExternalBuyerChat(
    payload: ExternalBuyerChatRequest
  ): Promise<ApiResponse<ExternalBuyerChatResponse>> {
    return request<ApiResponse<ExternalBuyerChatResponse>>("/api/external-buyer/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};


