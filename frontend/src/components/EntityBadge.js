import React from "react";
import { Building2, Users } from "lucide-react";

/**
 * Visual badge distinguishing Companies (blue) from LLPs (purple).
 * Colors are drawn from the design token hues used across the app.
 */
export function EntityBadge({ type, className = "" }) {
  const isLLP = (type || "Company") === "LLP";
  const Icon = isLLP ? Users : Building2;
  const cls = isLLP
    ? "bg-[hsl(270_60%_95%)] text-[hsl(270_50%_40%)] dark:bg-[hsl(270_40%_22%)] dark:text-[hsl(270_60%_80%)]"
    : "bg-[hsl(199_78%_94%)] text-[hsl(199_78%_30%)] dark:bg-[hsl(199_78%_18%)] dark:text-[hsl(199_78%_72%)]";
  return (
    <span
      data-testid="entity-badge"
      className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${cls} ${className}`}
    >
      <Icon className="h-3 w-3" /> {isLLP ? "LLP" : "Company"}
    </span>
  );
}
