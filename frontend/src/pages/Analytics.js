import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Building2, Users } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { RegistrationTrend } from "@/components/charts/RegistrationTrend";
import { SectorBreakdown } from "@/components/charts/SectorBreakdown";
import { CapitalDistribution } from "@/components/charts/CapitalDistribution";
import { ChartSkeleton } from "@/components/Skeletons";
import { getTrends, getSectors, getCapital, getHeatmap, getSummary } from "@/lib/api";
import { formatINR, formatNumber } from "@/lib/format";

const CITY_TABS = ["All", "Mumbai", "Navi Mumbai", "Thane"];

export default function Analytics() {
  const [city, setCity] = useState("All");
  const { data: trends, isLoading: lt } = useQuery({ queryKey: ["a-trends", city], queryFn: () => getTrends(city, 24) });
  const { data: sectors, isLoading: ls } = useQuery({ queryKey: ["a-sectors", city], queryFn: () => getSectors(city, 20) });
  const { data: capital, isLoading: lc } = useQuery({ queryKey: ["a-capital", city], queryFn: () => getCapital(city) });
  const { data: heatmap, isLoading: lh } = useQuery({ queryKey: ["a-heatmap", city], queryFn: () => getHeatmap(city) });
  const { data: summary, isLoading: lsum } = useQuery({ queryKey: ["a-summary", city], queryFn: () => getSummary(city) });

  const maxArea = Math.max(1, ...((heatmap?.heatmap || []).map((h) => h.count)));
  const ent = summary?.by_entity_type || {};
  const companies = summary?.companies_count ?? ent.Company ?? 0;
  const llps = summary?.llps_count ?? ent.LLP ?? 0;
  const totalEnt = companies + llps;
  const compPct = totalEnt ? (companies / totalEnt) * 100 : 0;
  const llpPct = totalEnt ? (llps / totalEnt) * 100 : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-heading text-2xl font-bold">Analytics</h1>
          <p className="text-sm text-muted-foreground">Market intelligence across the Mumbai Metropolitan Region</p>
        </div>
        <Tabs value={city} onValueChange={setCity} data-testid="analytics-city-tabs" className="w-full sm:w-auto overflow-x-auto">
          <TabsList className="min-w-max">
            {CITY_TABS.map((c) => <TabsTrigger key={c} value={c} data-testid={`analytics-city-${c.replace(/\s/g, '-').toLowerCase()}`}>{c}</TabsTrigger>)}
          </TabsList>
        </Tabs>
      </div>

      <Card className="p-4 xs:p-5" data-testid="analytics-trend-chart">
        <h3 className="font-heading text-sm font-semibold mb-4">Monthly new registrations (last 24 months)</h3>
        {lt ? <ChartSkeleton h={320} /> : <RegistrationTrend data={trends?.trends || []} height={320} />}
      </Card>

      {/* Company vs LLP breakdown */}
      <Card className="p-4 xs:p-5" data-testid="analytics-entity-breakdown">
        <h3 className="font-heading text-sm font-semibold mb-4">Company vs LLP</h3>
        {lsum ? <ChartSkeleton h={120} /> : (
          <>
            <div className="grid grid-cols-1 mb:grid-cols-2 gap-3 xs:gap-4">
              <div className="rounded-lg border p-4" data-testid="analytics-companies-tile">
                <div className="flex items-center gap-2 text-[hsl(199_78%_36%)]">
                  <Building2 className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wide">Companies</span>
                </div>
                <div className="mt-2 font-heading text-2xl font-bold tabular-nums">{formatNumber(companies)}</div>
                <div className="text-xs text-muted-foreground">{compPct.toFixed(1)}% of entities</div>
              </div>
              <div className="rounded-lg border p-4" data-testid="analytics-llps-tile">
                <div className="flex items-center gap-2 text-[hsl(270_50%_45%)]">
                  <Users className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wide">LLPs</span>
                </div>
                <div className="mt-2 font-heading text-2xl font-bold tabular-nums">{formatNumber(llps)}</div>
                <div className="text-xs text-muted-foreground">{llpPct.toFixed(1)}% of entities</div>
              </div>
            </div>
            <div className="mt-4 flex h-3 w-full overflow-hidden rounded-full bg-muted" role="img" aria-label="Company vs LLP split">
              <div className="h-full bg-[hsl(199_78%_46%)]" style={{ width: `${compPct}%` }} />
              <div className="h-full bg-[hsl(270_50%_55%)]" style={{ width: `${llpPct}%` }} />
            </div>
          </>
        )}
      </Card>

      <div className="grid lg:grid-cols-2 gap-4">
        <Card className="p-4 xs:p-5" data-testid="analytics-sectors-bar">
          <h3 className="font-heading text-sm font-semibold mb-4">Top sectors</h3>
          {ls ? <ChartSkeleton h={400} /> : <SectorBreakdown data={sectors?.sectors || []} height={420} />}
        </Card>
        <Card className="p-4 xs:p-5">
          <h3 className="font-heading text-sm font-semibold mb-4">Paid-up capital distribution</h3>
          {lc ? <ChartSkeleton h={400} /> : <CapitalDistribution data={capital?.distribution || []} height={420} />}
        </Card>
      </div>

      {/* Heatmap */}
      <Card className="p-4 xs:p-5" data-testid="analytics-heatmap">
        <h3 className="font-heading text-sm font-semibold mb-4">Area-wise company density</h3>
        {lh ? <ChartSkeleton h={180} /> : (
          <div className="grid grid-cols-1 mb:grid-cols-2 xs:grid-cols-3 lg:grid-cols-4 gap-2">
            {(heatmap?.heatmap || []).slice(0, 24).map((h, i) => {
              const intensity = 0.12 + (h.count / maxArea) * 0.7;
              return (
                <div key={i} className="rounded-lg border p-3" style={{ background: `hsl(var(--chart-1) / ${intensity})` }}>
                  <div className="text-xs font-medium text-foreground truncate">{h.area}</div>
                  <div className="text-[10px] text-muted-foreground">{h.city}</div>
                  <div className="mt-1 font-heading text-lg font-bold tabular-nums">{formatNumber(h.count)}</div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Sector table */}
      <Card className="p-2 sm:p-4">
        <h3 className="font-heading text-sm font-semibold p-2">Sector breakdown</h3>
        <Table>
          <TableHeader><TableRow><TableHead>Sector</TableHead><TableHead className="text-right">Companies</TableHead><TableHead className="text-right">Avg paid-up capital</TableHead></TableRow></TableHeader>
          <TableBody>
            {(sectors?.sectors || []).map((s) => (
              <TableRow key={s.sector}>
                <TableCell className="font-medium">{s.sector}</TableCell>
                <TableCell className="text-right tabular-nums">{formatNumber(s.count)}</TableCell>
                <TableCell className="text-right tabular-nums">{formatINR(s.avg_capital)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
