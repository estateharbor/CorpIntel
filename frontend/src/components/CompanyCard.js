import React from "react";
import { Link } from "react-router-dom";
import { Users, Calendar, IndianRupee, ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/StatusBadge";
import { CityTag, SectorChip } from "@/components/CityTag";
import { formatINR, formatDate } from "@/lib/format";

export function CompanyCard({ company }) {
  const c = company;
  return (
    <Card
      data-testid="company-card"
      className="group p-4 transition-shadow transition-colors duration-150 hover:shadow-soft hover:border-accent/40"
    >
      <div className="flex items-start justify-between gap-3">
        <Link
          to={`/company/${c.cin}`}
          className="min-w-0 font-heading font-semibold text-[15px] leading-snug hover:text-accent transition-colors"
          data-testid="company-card-name"
        >
          {c.name}
        </Link>
        <StatusBadge status={c.status} />
      </div>
      <div className="mt-1 font-mono text-[11px] text-muted-foreground">{c.cin}</div>

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
          <span className="text-foreground tabular-nums">{formatINR(c.paid_up_capital)}</span>
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <Users className="h-4 w-4" />
          <span className="text-foreground tabular-nums">{c.director_count} directors</span>
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <span className="inline-flex h-1.5 w-1.5 rounded-full bg-accent" />
          <span className="text-foreground tabular-nums">DQ {c.data_quality_score}/100</span>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{c.company_class}</span>
        <Link
          to={`/company/${c.cin}`}
          data-testid="company-card-view"
          className="inline-flex items-center gap-1 text-xs font-medium text-accent hover:underline"
        >
          View profile <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    </Card>
  );
}
