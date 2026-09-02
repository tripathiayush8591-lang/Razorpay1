import React from "react";
import { Navigate, useLocation, Outlet } from "react-router-dom";
import { useAdminAuth } from "@/lib/auth/AdminAuthContext";
import { Shield } from "lucide-react";

export const AdminProtectedRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAdminAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center text-accent-foreground animate-pulse">
          <Shield className="w-5 h-5" />
        </div>
        <p className="text-xs text-text-secondary font-medium">Verifying admin session...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/admin/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
};

export default AdminProtectedRoute;
