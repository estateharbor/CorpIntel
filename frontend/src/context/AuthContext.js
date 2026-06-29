import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import api from "@/lib/api";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
    } catch (e) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // CRITICAL: If returning from OAuth callback, skip the /me check.
    // AuthCallback will exchange the session_id and establish the session first.
    if (typeof window !== "undefined" && window.location.hash?.includes("session_id=")) {
      setLoading(false);
      return;
    }
    checkAuth();
  }, [checkAuth]);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    localStorage.setItem("ci_token", data.access_token);
    setUser(data.user);
    return data.user;
  };

  const register = async (email, password, name) => {
    const { data } = await api.post("/auth/register", { email, password, name });
    localStorage.setItem("ci_token", data.access_token);
    setUser(data.user);
    return data.user;
  };

  const demoLogin = async () => {
    const { data } = await api.post("/auth/demo-login");
    localStorage.setItem("ci_token", data.access_token);
    setUser(data.user);
    return data.user;
  };

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const googleLogin = () => {
    const redirectUrl = window.location.origin + "/dashboard";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch (e) {
      /* ignore */
    }
    localStorage.removeItem("ci_token");
    setUser(null);
  };

  const value = { user, loading, login, register, demoLogin, googleLogin, logout, refresh: checkAuth, setUser };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
