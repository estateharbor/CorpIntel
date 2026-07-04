import React from "react";
import { CheckCircle2, XCircle, AlertTriangle } from "lucide-react";

const MAP = {
  Active: { cls: "bg-[hsl(var(--status-active-bg))] text-[hsl(var(--status-active-fg))]", Icon: CheckCircle2 },
  "Struck Off": { cls: "bg-[hsl(var(--status-struck-bg))] text-[hsl(var(--status-struck-fg))]", Icon: XCircle },
  "Under Liquidation": { cls: "bg-[hsl(var(--status-liq-bg))] text-[hsl(var(--status-liq-fg))]", Icon: AlertTriangle },
};

export function StatusBadge({ status, className = "" }) {
  const cfg = MAP[status] || MAP.Active;
  const Icon = cfg.Icon;
  return (
    <span
      data-testid="company-status-badge"
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${cfg.cls} ${className}`}
    >
      <Icon className="h-3.5 w-3.5" />
      {status}
    </span>
  );
}
