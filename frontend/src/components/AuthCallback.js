import React, { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function AuthCallback() {
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const processed = useRef(false);

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;
    const hash = window.location.hash || "";
    const match = hash.match(/session_id=([^&]+)/);
    const sid = match ? decodeURIComponent(match[1]) : null;
    (async () => {
      if (sid) {
        try {
          await api.post("/auth/google/session", { session_id: sid });
          await refresh();
        } catch (e) {
          /* ignore - will land on dashboard, may need login */
        }
      }
      window.history.replaceState({}, document.title, window.location.pathname);
      navigate("/dashboard", { replace: true });
    })();
  }, [navigate, refresh]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background" data-testid="auth-callback">
      <div className="flex flex-col items-center gap-3 text-muted-foreground">
        <Loader2 className="h-7 w-7 animate-spin text-accent" />
        <p className="text-sm">Signing you in…</p>
      </div>
    </div>
  );
}
