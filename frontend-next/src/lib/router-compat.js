"use client";

import NextLink from "next/link";
import { useParams as useNextParams, usePathname, useRouter, useSearchParams } from "next/navigation";
import React from "react";

export function Link({ to, href, children, ...props }) {
  return (
    <NextLink href={href || to || "#"} {...props}>
      {children}
    </NextLink>
  );
}

export function NavLink({ to, className, children, ...props }) {
  const pathname = usePathname();
  const href = to || props.href || "#";
  const isActive = pathname === href || (href !== "/" && pathname?.startsWith(href));
  const resolvedClassName = typeof className === "function" ? className({ isActive }) : className;
  const resolvedChildren = typeof children === "function" ? children({ isActive }) : children;

  return (
    <NextLink href={href} className={resolvedClassName} {...props}>
      {resolvedChildren}
    </NextLink>
  );
}

export function useNavigate() {
  const router = useRouter();
  return React.useCallback((to, options = {}) => {
    if (typeof to === "number") {
      window.history.go(to);
      return;
    }
    if (options.replace) {
      router.replace(to);
    } else {
      router.push(to);
    }
  }, [router]);
}

export function useLocation() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const search = searchParams?.toString();
  return {
    pathname,
    search: search ? `?${search}` : "",
    state: null,
  };
}

export function useParams() {
  return useNextParams();
}

export function Navigate({ to, replace = false }) {
  const router = useRouter();
  React.useEffect(() => {
    if (replace) {
      router.replace(to);
    } else {
      router.push(to);
    }
  }, [replace, router, to]);
  return null;
}

export function Outlet() {
  return null;
}

export function BrowserRouter({ children }) {
  return children;
}

export function Routes({ children }) {
  return children;
}

export function Route() {
  return null;
}
