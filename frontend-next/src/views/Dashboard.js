"use client";

import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Building2, TrendingUp, Activity, Layers, ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/StatusBadge";
import { RegistrationTrend } from "@/components/charts/RegistrationTrend";
import { CityDistribution } from "@/components/charts/CityDistribution";
import { SectorBreakdown } from "@/components/charts/SectorBreakdown";
import { CapitalDistribution } from "@/components/charts/CapitalDistribution";
import { KpiSkeleton, ChartSkeleton } from "@/components/Skeletons";
import { getSummary, getTrends, getSectors, getCapital, getCompanies } from "@/lib/api";
import { formatNumber, formatINR, formatDate } from "@/lib/format";

function Kpi({ label, value, sub, icon: Icon, testid }) {
  return (
    <Card className="p-4" data-testid={testid}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{label}</span>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary dark:bg-white/5 dark:text-foreground">
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <div className="mt-2 font-heading text-2xl sm:text-3xl font-bold tabular-nums">{value}</div>
      {sub && <div className="mt-1 text-xs text-muted-foreground">{sub}</div>}
    </Card>
  );
}

export default function Dashboard() {
  const { data: summary, isLoading: ls } = useQuery({ queryKey: ["summary"], queryFn: () => getSummary("All") });
  const { data: trends, isLoading: lt } = useQuery({ queryKey: ["trends", 12], queryFn: () => getTrends("All", 12) });
  const { data: sectors, isLoading: lsec } = useQuery({ queryKey: ["sectors-dash"], queryFn: () => getSectors("All", 10) });
  const { data: capital, isLoading: lc } = useQuery({ queryKey: ["capital-dash"], queryFn: () => getCapital("All") });
  const { data: recent } = useQuery({ queryKey: ["recent"], queryFn: () => getCompanies({ sort_by: "date_of_incorporation", order: "desc", limit: 10 }) });

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-2">
        <div>
          <h1 className="font-heading text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">MMR company intelligence overview</p>
        </div>
        <Link to="/search" className="text-sm text-accent hover:underline inline-flex items-center gap-1">
          Browse all companies <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 mb:grid-cols-2 lg:grid-cols-4 gap-4">
        {ls ? (
          Array.from({ length: 4 }).map((_, i) => <KpiSkeleton key={i} />)
        ) : (
          <>
            <Kpi testid="dashboard-kpi-total-companies" label="Total companies" value={formatNumber(summary?.total)} sub={`Mumbai ${formatNumber(summary?.by_city?.Mumbai || 0)} · NM ${formatNumber(summary?.by_city?.["Navi Mumbai"] || 0)} · Thane ${formatNumber(summary?.by_city?.Thane || 0)}`} icon={Building2} />
            <Kpi testid="dashboard-kpi-new-week" label="New this week" value={formatNumber(summary?.new_this_week)} sub="Last 7 days" icon={TrendingUp} />
            <Kpi testid="dashboard-kpi-active" label="Active ratio" value={`${summary?.active_ratio ?? 0}%`} sub={`${formatNumber(summary?.active)} active · ${formatNumber(summary?.struck_off)} struck off`} icon={Activity} />
            <Kpi testid="dashboard-kpi-top-sector" label="Top sector" value={summary?.top_sector?.sector?.split(" ")[0] || "—"} sub={`${formatNumber(summary?.top_sector?.count || 0)} companies`} icon={Layers} />
          </>
        )}
      </div>

      {/* Charts */}
      <div className="grid lg:grid-cols-3 gap-4">
        <Card className="p-4 xs:p-5 lg:col-span-2" data-testid="dashboard-chart-registrations-trend">
          <h3 className="font-heading text-sm font-semibold mb-4">New registrations (last 12 months)</h3>
          {lt ? <ChartSkeleton /> : <RegistrationTrend data={trends?.trends || []} />}
        </Card>
        <Card className="p-4 xs:p-5" data-testid="dashboard-chart-city-distribution">
          <h3 className="font-heading text-sm font-semibold mb-4">City distribution</h3>
          {ls ? <ChartSkeleton /> : <CityDistribution byCity={summary?.by_city || {}} />}
        </Card>
      </div>
      <div className="grid lg:grid-cols-2 gap-4">
        <Card className="p-4 xs:p-5">
          <h3 className="font-heading text-sm font-semibold mb-4">Top 10 sectors</h3>
          {lsec ? <ChartSkeleton /> : <SectorBreakdown data={sectors?.sectors || []} height={340} />}
        </Card>
        <Card className="p-4 xs:p-5">
          <h3 className="font-heading text-sm font-semibold mb-4">Paid-up capital distribution</h3>
          {lc ? <ChartSkeleton /> : <CapitalDistribution data={capital?.distribution || []} />}
        </Card>
      </div>

      {/* Recent activity */}
      <Card className="p-5" data-testid="dashboard-recent-activity-table">
        <h3 className="font-heading text-sm font-semibold mb-4">Recently registered companies</h3>
        <div className="divide-y">
          {(recent?.results || []).map((c) => (
            <Link key={c.cin} to={`/company/${c.cin}`} className="flex items-center gap-3 py-2.5 hover:bg-muted/50 rounded-md px-2 -mx-2 transition-colors">
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10 text-primary dark:bg-white/5 dark:text-foreground shrink-0">
                <Building2 className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">{c.name}</div>
                <div className="truncate text-xs text-muted-foreground">{c.city} · {c.sector} · {formatDate(c.date_of_incorporation)}</div>
              </div>
              <span className="hidden xs:block text-xs text-muted-foreground tabular-nums">{formatINR(c.paid_up_capital)}</span>
              <StatusBadge status={c.status} />
            </Link>
          ))}
        </div>
      </Card>
    </div>
  );
}
