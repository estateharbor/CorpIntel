import React from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip, Cell,
} from "recharts";
import { ChartTooltip } from "@/components/charts/ChartTooltip";

const COLORS = ["hsl(var(--chart-1))", "hsl(var(--chart-2))", "hsl(var(--chart-3))", "hsl(var(--chart-4))", "hsl(var(--chart-5))"];

export function SectorBreakdown({ data = [], height = 360, layout = "vertical" }) {
  const rows = data.map((d) => ({ sector: d.sector, count: d.count }));
  if (layout === "vertical") {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }}>
          <CartesianGrid stroke="hsl(var(--gridline))" strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} />
          <YAxis type="category" dataKey="sector" width={150} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} tickLine={false} axisLine={false} />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: "hsl(var(--muted))", opacity: 0.4 }} />
          <Bar dataKey="count" name="Companies" radius={[0, 6, 6, 0]}>
            {rows.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={rows} margin={{ top: 4, right: 12, left: -8, bottom: 4 }}>
        <CartesianGrid stroke="hsl(var(--gridline))" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="sector" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} tickLine={false} axisLine={false} angle={-30} textAnchor="end" height={70} interval={0} />
        <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} width={36} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: "hsl(var(--muted))", opacity: 0.4 }} />
        <Bar dataKey="count" name="Companies" radius={[6, 6, 0, 0]} fill="hsl(var(--chart-1))" />
      </BarChart>
    </ResponsiveContainer>
  );
}
