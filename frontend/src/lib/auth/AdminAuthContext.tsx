import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import type { AdminUser } from "@/types/domain";
import { apiClient } from "@/lib/api/client";

interface AdminAuthContextType {
  admin: AdminUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AdminAuthContext = createContext<AdminAuthContextType | null>(null);

export const AdminAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [admin, setAdmin] = useState<AdminUser | null>(null);
  const [token, setToken] = useState<string | null>(() => {
    return typeof window !== "undefined" ? sessionStorage.getItem("admin_token") : null;
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const logout = useCallback(() => {
    sessionStorage.removeItem("admin_token");
    setToken(null);
    setAdmin(null);
  }, []);

  const verifySession = useCallback(async () => {
    const storedToken = sessionStorage.getItem("admin_token");
    if (!storedToken) {
      setIsLoading(false);
      return;
    }

    try {
      const res = await apiClient.getAdminMe();
      if (res.success && res.data) {
        setAdmin(res.data);
        setToken(storedToken);
      } else {
        logout();
      }
    } catch {
      logout();
    } finally {
      setIsLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    verifySession();
  }, [verifySession]);

  const login = async (email: string, password: string) => {
    const res = await apiClient.adminLogin(email, password);
    if (!res.success || !res.data) {
      throw new Error(res.error?.message || "Login failed");
    }

    const { token: receivedToken, admin: adminData } = res.data;
    sessionStorage.setItem("admin_token", receivedToken);
    setToken(receivedToken);
    setAdmin(adminData);
  };

  return (
    <AdminAuthContext.Provider
      value={{
        admin,
        token,
        isAuthenticated: Boolean(token && admin),
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AdminAuthContext.Provider>
  );
};

export const useAdminAuth = () => {
  const context = useContext(AdminAuthContext);
  if (!context) {
    throw new Error("useAdminAuth must be used within an AdminAuthProvider");
  }
  return context;
};
