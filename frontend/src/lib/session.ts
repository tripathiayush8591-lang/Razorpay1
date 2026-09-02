/**
 * Client Guest Session Manager
 * Generates and persists a stable guest session identifier in localStorage.
 * Ensures carts and quotes remain stable across page reloads without requiring user accounts.
 */

const GUEST_SESSION_KEY = "runcraft_guest_session_id";

export function getOrCreateGuestSessionId(): string {
  if (typeof window === "undefined") {
    return "server_rendered_session";
  }

  try {
    let sessionId = localStorage.getItem(GUEST_SESSION_KEY);
    if (!sessionId || !sessionId.trim()) {
      sessionId = `guest_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`;
      localStorage.setItem(GUEST_SESSION_KEY, sessionId);
    }
    return sessionId;
  } catch {
    return "fallback_guest_session";
  }
}
