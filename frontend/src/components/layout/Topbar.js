import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { Menu, LogOut, User as UserIcon, LayoutDashboard } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { QuickSearch } from "@/components/QuickSearch";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { useAuth } from "@/context/AuthContext";

export function Topbar({ onMenuClick }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const initials = (user?.name || user?.email || "U").slice(0, 2).toUpperCase();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b bg-topbar px-4 sm:px-6">
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={onMenuClick}
        data-testid="topbar-menu-button"
        aria-label="Open menu"
      >
        <Menu className="h-5 w-5" />
      </Button>

      <div className="flex-1 flex justify-start">
        <QuickSearch />
      </div>

      <div className="flex items-center gap-1.5">
        <ThemeToggle />
        {user ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="gap-2 px-2" data-testid="topbar-user-menu">
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="bg-primary text-primary-foreground text-xs">{initials}</AvatarFallback>
                </Avatar>
                <span className="hidden sm:block text-sm font-medium max-w-[120px] truncate">{user.name}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel className="truncate">{user.email}</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate("/dashboard")}>
                <LayoutDashboard className="mr-2 h-4 w-4" /> Dashboard
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate("/settings")} data-testid="menu-settings">
                <UserIcon className="mr-2 h-4 w-4" /> Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout} data-testid="menu-logout">
                <LogOut className="mr-2 h-4 w-4" /> Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <Button asChild className="bg-accent text-accent-foreground hover:brightness-95" data-testid="topbar-signin">
            <Link to="/login">Sign in</Link>
          </Button>
        )}
      </div>
    </header>
  );
}
