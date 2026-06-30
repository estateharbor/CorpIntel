import { LayoutDashboard, Search, BarChart3, Bell, Download, Tag, Settings, Database } from "lucide-react";

export const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, testid: "nav-dashboard" },
  { to: "/search", label: "Search", icon: Search, testid: "nav-search" },
  { to: "/analytics", label: "Analytics", icon: BarChart3, testid: "nav-analytics" },
  { to: "/alerts", label: "Alerts", icon: Bell, testid: "nav-alerts", auth: true },
  { to: "/export", label: "Export", icon: Download, testid: "nav-export", auth: true },
  { to: "/admin/enrichment", label: "MCA Enrichment", icon: Database, testid: "nav-admin-enrichment", auth: true },
  { to: "/pricing", label: "Pricing", icon: Tag, testid: "nav-pricing" },
  { to: "/settings", label: "Settings", icon: Settings, testid: "nav-settings", auth: true },
];
