import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/context/AuthContext";
import AppShell from "@/components/layout/AppShell";
import ProtectedRoute from "@/components/ProtectedRoute";
import AuthCallback from "@/components/AuthCallback";

import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import SearchPage from "@/pages/Search";
import CompanyDetail from "@/pages/CompanyDetail";
import Analytics from "@/pages/Analytics";
import Alerts from "@/pages/Alerts";
import ExportPage from "@/pages/Export";
import Pricing from "@/pages/Pricing";
import Settings from "@/pages/Settings";
import AdminEnrichment from "@/pages/AdminEnrichment";

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1, staleTime: 30000 } },
});

function AppRouter() {
  const location = useLocation();
  // Handle Emergent Google OAuth callback BEFORE any protected routing
  if (location.hash && location.hash.includes("session_id=")) {
    return <AuthCallback />;
  }
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route element={<AppShell />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/company/:cin" element={<CompanyDetail />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/alerts" element={<ProtectedRoute><Alerts /></ProtectedRoute>} />
        <Route path="/export" element={<ProtectedRoute><ExportPage /></ProtectedRoute>} />
        <Route path="/admin/enrichment" element={<ProtectedRoute><AdminEnrichment /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
            <AppRouter />
            <Toaster richColors position="top-right" />
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;
