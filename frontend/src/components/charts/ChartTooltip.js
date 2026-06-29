import React from "react";

// Shared custom tooltip for Recharts that respects theme tokens.
export function ChartTooltip({ active, payload, label, valueFormatter }) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-lg border bg-card px-3 py-2 shadow-soft">
      {label !== undefined && <div className="mb-1 text-xs font-medium text-foreground">{label}</div>}
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2 text-xs">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: p.color || p.fill }} />
          <span className="text-muted-foreground">{p.name}:</span>
          <span className="font-medium text-foreground tabular-nums">
            {valueFormatter ? valueFormatter(p.value) : p.value}
          </span>
        </div>
      ))}
    </div>
  );
}
