import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MockCommerceProvider } from "./lib/mock/MockCommerceContext";
import { AdminAuthProvider } from "./lib/auth/AdminAuthContext";
import AdminProtectedRoute from "./components/admin/AdminProtectedRoute";
import AppShell from "./components/layout/AppShell";
import LandingPage from "./components/storefront/LandingPage";
import ShopPage from "./pages/client/ShopPage";
import ProductDetailPage from "./pages/client/ProductDetailPage";
import AssistantPanel from "./components/assistant/AssistantPanel";
import CartPage from "./pages/client/CartPage";
import CheckoutPage from "./pages/client/CheckoutPage";
import OrdersPage from "./pages/client/OrdersPage";
import OrderDetailPage from "./pages/client/OrderDetailPage";
import AdminShell from "./components/layout/AdminShell";
import AdminLogin from "./pages/admin/AdminLogin";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminCatalog from "./pages/admin/AdminCatalog";
import SkuForm from "./components/admin/SkuForm";
import AdminOrders from "./pages/admin/AdminOrders";
import AdminOrderDetail from "./pages/admin/AdminOrderDetail";
import AdminPolicies from "./pages/admin/AdminPolicies";
import AdminChannels from "./pages/admin/AdminChannels";
import ExternalBuyerPage from "./pages/client/ExternalBuyerPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30, // 30 seconds
      refetchOnWindowFocus: false,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AdminAuthProvider>
        <MockCommerceProvider>
          <BrowserRouter>
            <Routes>
              {/* Client Storefront Shell */}
              <Route path="/" element={<AppShell />}>
                <Route index element={<LandingPage />} />
                <Route path="shop" element={<ShopPage />} />
                <Route path="product/:productId" element={<ProductDetailPage />} />
                <Route
                  path="assistant"
                  element={
                    <div className="py-2 max-w-4xl mx-auto">
                      <AssistantPanel isFullPage />
                    </div>
                  }
                />
                <Route path="cart" element={<CartPage />} />
                <Route path="checkout" element={<CheckoutPage />} />
                <Route path="orders" element={<OrdersPage />} />
                <Route path="orders/:orderId" element={<OrderDetailPage />} />
                <Route path="external-buyer" element={<ExternalBuyerPage />} />
              </Route>

              {/* Admin Login (Unwrapped) */}
              <Route path="/admin/login" element={<AdminLogin />} />

              {/* Protected Admin Portal */}
              <Route path="/admin" element={<AdminProtectedRoute />}>
                <Route element={<AdminShell />}>
                  <Route index element={<Navigate to="/admin/dashboard" replace />} />
                  <Route path="dashboard" element={<AdminDashboard />} />
                  <Route path="catalog" element={<AdminCatalog />} />
                  <Route path="catalog/new" element={<SkuForm />} />
                  <Route path="catalog/:skuId/edit" element={<SkuForm />} />
                  <Route path="orders" element={<AdminOrders />} />
                  <Route path="orders/:orderId" element={<AdminOrderDetail />} />
                  <Route path="policies" element={<AdminPolicies />} />
                  <Route path="channels" element={<AdminChannels />} />
                </Route>
              </Route>

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </MockCommerceProvider>
      </AdminAuthProvider>
    </QueryClientProvider>
  );
}

export default App;
