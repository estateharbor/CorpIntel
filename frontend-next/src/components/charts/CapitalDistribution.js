import React from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip,
} from "recharts";
import { ChartTooltip } from "@/components/charts/ChartTooltip";

export function CapitalDistribution({ data = [], height = 300 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 12, left: -8, bottom: 4 }}>
        <CartesianGrid stroke="hsl(var(--gridline))" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="range" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} tickLine={false} axisLine={false} angle={-20} textAnchor="end" height={54} interval={0} />
        <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} width={36} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: "hsl(var(--muted))", opacity: 0.4 }} />
        <Bar dataKey="count" name="Companies" radius={[6, 6, 0, 0]} fill="hsl(var(--chart-2))" />
      </BarChart>
    </ResponsiveContainer>
  );
}
