import React from "react";
import { NavLink } from "react-router-dom";
import { Building2, Sparkles } from "lucide-react";
import { NAV_ITEMS } from "@/lib/nav";
import { useAuth } from "@/context/AuthContext";
import { Badge } from "@/components/ui/badge";

export function Sidebar({ onNavigate }) {
  const { user } = useAuth();
  return (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex items-center gap-2.5 px-5 h-16 border-b border-white/10">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
          <Building2 className="h-5 w-5" />
        </div>
        <div className="leading-tight">
          <div className="font-heading font-bold text-[15px] tracking-tight">CorpIntel</div>
          <div className="text-[11px] text-sidebar-foreground/60 -mt-0.5">India · MMR Intelligence</div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto thin-scroll">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onNavigate}
              data-testid={item.testid}
              className={({ isActive }) =>
                `group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-white/10 text-white"
                    : "text-sidebar-foreground/70 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-full bg-accent" />
                  )}
                  <Icon className="h-[18px] w-[18px]" />
                  <span>{item.label}</span>
                  {item.auth && !user && (
                    <span className="ml-auto text-[10px] text-sidebar-foreground/40">sign in</span>
                  )}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="p-3 border-t border-white/10">
        <div className="rounded-lg bg-white/5 p-3">
          <div className="flex items-center gap-2 text-xs text-sidebar-foreground/70">
            <Sparkles className="h-3.5 w-3.5 text-accent" />
            {user ? (
              <span>
                Plan: <Badge className="bg-accent text-accent-foreground capitalize">{user.plan}</Badge>
              </span>
            ) : (
              <span>Free preview · sign in to unlock</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
