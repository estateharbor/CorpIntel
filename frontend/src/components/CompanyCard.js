import React from "react";
import { Link } from "react-router-dom";
import { Users, Calendar, IndianRupee, ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/StatusBadge";
import { EntityBadge } from "@/components/EntityBadge";
import { CityTag, SectorChip } from "@/components/CityTag";
import { formatINR, formatDate } from "@/lib/format";

export function CompanyCard({ company }) {
  const c = company;
  const id = c.identifier || c.cin;
  const isLLP = c.entity_type === "LLP";
  return (
    <Card
      data-testid="company-card"
      className="group p-4 transition-shadow transition-colors duration-150 hover:shadow-soft hover:border-accent/40"
    >
      <div className="flex items-start justify-between gap-3">
        <Link
          to={`/company/${id}`}
          className="min-w-0 font-heading font-semibold text-[15px] leading-snug hover:text-accent transition-colors"
          data-testid="company-card-name"
        >
          {c.name}
        </Link>
        <div className="flex items-center gap-1.5 shrink-0">
          <EntityBadge type={c.entity_type} />
          <StatusBadge status={c.status} />
        </div>
      </div>
      <div className="mt-1 font-mono text-[11px] text-muted-foreground">{id}</div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        <CityTag city={c.city} area={c.area} />
        <SectorChip sector={c.sector} />
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Calendar className="h-4 w-4" />
          <span className="text-foreground">{formatDate(c.date_of_incorporation)}</span>
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <IndianRupee className="h-4 w-4" />
          <span className="text-foreground tabular-nums">
            {formatINR(isLLP && c.total_contribution != null ? c.total_contribution : c.paid_up_capital)}
          </span>
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <Users className="h-4 w-4" />
          <span className="text-foreground tabular-nums">
            {c.director_count} {isLLP ? "partners" : "directors"}
          </span>
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <span className="inline-flex h-1.5 w-1.5 rounded-full bg-accent" />
          <span className="text-foreground tabular-nums">DQ {c.data_quality_score}/100</span>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{c.company_class}</span>
        <Link
          to={`/company/${id}`}
          data-testid="company-card-view"
          className="inline-flex items-center gap-1 text-xs font-medium text-accent hover:underline"
        >
          View profile <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    </Card>
  );
}
