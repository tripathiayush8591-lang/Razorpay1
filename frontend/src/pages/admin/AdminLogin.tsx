import React, { useState } from "react";
import { useNavigate, Link, useLocation } from "react-router-dom";
import { Shield, Lock, ArrowLeft, AlertCircle, CheckCircle2 } from "lucide-react";
import { useAdminAuth } from "../../lib/auth/AdminAuthContext";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";

export const AdminLogin: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAdminAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const redirectPath = (location.state as { from?: { pathname?: string } })?.from?.pathname || "/admin/dashboard";

  // If already authenticated, redirect
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate(redirectPath, { replace: true });
    }
  }, [isAuthenticated, navigate, redirectPath]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage(null);

    try {
      await login(email, password);
      navigate(redirectPath, { replace: true });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Invalid credentials. Please verify your email and password.";
      setErrorMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center px-4 py-12 antialiased">
      <div className="max-w-md w-full space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-accent flex items-center justify-center text-accent-foreground mx-auto shadow-sm">
            <Shield className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold text-text-primary">RunCraft Merchant Portal</h1>
          <p className="text-xs text-text-secondary">
            Sign in to manage catalog SKUs, inspect orders, and configure AI agent policies.
          </p>
        </div>

        {/* Demo Mode Explainer Banner */}
        <div className="p-3.5 rounded-xl bg-accent-muted border border-accent/20 flex items-start gap-3 text-xs">
          <CheckCircle2 className="w-4 h-4 text-accent shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-text-primary">Authoritative Admin Session</p>
            <p className="text-text-secondary leading-relaxed">
              FastAPI generates a 24-hour cryptographically signed Bearer session token stored safely in sessionStorage.
            </p>
          </div>
        </div>

        {/* Error alert */}
        {errorMessage && (
          <div className="p-3.5 rounded-xl bg-error-light border border-error/20 flex items-center gap-2.5 text-xs text-error-foreground animate-in fade-in duration-200">
            <AlertCircle className="w-4 h-4 text-error shrink-0" />
            <span className="font-medium">{errorMessage}</span>
          </div>
        )}

        {/* Card Form */}
        <div className="bg-surface rounded-2xl border border-border p-6 sm:p-8 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Merchant Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <Input
              label="Admin Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                size="md"
                className="w-full justify-center"
                loading={loading}
                icon={<Lock className="w-4 h-4" />}
              >
                Sign In to Merchant Portal
              </Button>
            </div>
          </form>

          <div className="mt-6 pt-4 border-t border-border flex items-center justify-between text-xs text-text-secondary">
            <span>Seeded Demo Account</span>
            <span className="font-mono text-[11px] bg-surface-secondary px-2 py-0.5 rounded border border-border">
              Role: Master Admin
            </span>
          </div>
        </div>

        {/* Return to Storefront */}
        <div className="text-center">
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-text-secondary hover:text-text-primary transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Customer Storefront</span>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;
