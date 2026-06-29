import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { RegistrationTrend } from "@/components/charts/RegistrationTrend";
import { SectorBreakdown } from "@/components/charts/SectorBreakdown";
import { CapitalDistribution } from "@/components/charts/CapitalDistribution";
import { ChartSkeleton } from "@/components/Skeletons";
import { getTrends, getSectors, getCapital, getHeatmap } from "@/lib/api";
import { formatINR, formatNumber } from "@/lib/format";

const CITY_TABS = ["All", "Mumbai", "Navi Mumbai", "Thane"];

export default function Analytics() {
  const [city, setCity] = useState("All");
  const { data: trends, isLoading: lt } = useQuery({ queryKey: ["a-trends", city], queryFn: () => getTrends(city, 24) });
  const { data: sectors, isLoading: ls } = useQuery({ queryKey: ["a-sectors", city], queryFn: () => getSectors(city, 20) });
  const { data: capital, isLoading: lc } = useQuery({ queryKey: ["a-capital", city], queryFn: () => getCapital(city) });
  const { data: heatmap, isLoading: lh } = useQuery({ queryKey: ["a-heatmap", city], queryFn: () => getHeatmap(city) });

  const maxArea = Math.max(1, ...((heatmap?.heatmap || []).map((h) => h.count)));

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-heading text-2xl font-bold">Analytics</h1>
          <p className="text-sm text-muted-foreground">Market intelligence across the Mumbai Metropolitan Region</p>
        </div>
        <Tabs value={city} onValueChange={setCity} data-testid="analytics-city-tabs">
          <TabsList>
            {CITY_TABS.map((c) => <TabsTrigger key={c} value={c} data-testid={`analytics-city-${c.replace(/\s/g, '-').toLowerCase()}`}>{c}</TabsTrigger>)}
          </TabsList>
        </Tabs>
      </div>

      <Card className="p-5" data-testid="analytics-trend-chart">
        <h3 className="font-heading text-sm font-semibold mb-4">Monthly new registrations (last 24 months)</h3>
        {lt ? <ChartSkeleton h={320} /> : <RegistrationTrend data={trends?.trends || []} height={320} />}
      </Card>

      <div className="grid lg:grid-cols-2 gap-4">
        <Card className="p-5" data-testid="analytics-sectors-bar">
          <h3 className="font-heading text-sm font-semibold mb-4">Top sectors</h3>
          {ls ? <ChartSkeleton h={400} /> : <SectorBreakdown data={sectors?.sectors || []} height={420} />}
        </Card>
        <Card className="p-5">
          <h3 className="font-heading text-sm font-semibold mb-4">Paid-up capital distribution</h3>
          {lc ? <ChartSkeleton h={400} /> : <CapitalDistribution data={capital?.distribution || []} height={420} />}
        </Card>
      </div>

      {/* Heatmap */}
      <Card className="p-5" data-testid="analytics-heatmap">
        <h3 className="font-heading text-sm font-semibold mb-4">Area-wise company density</h3>
        {lh ? <ChartSkeleton h={180} /> : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
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
