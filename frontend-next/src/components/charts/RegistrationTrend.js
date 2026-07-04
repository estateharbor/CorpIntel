import React from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip,
} from "recharts";
import { ChartTooltip } from "@/components/charts/ChartTooltip";

export function RegistrationTrend({ data = [], height = 300 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
        <defs>
          <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="hsl(var(--chart-2))" stopOpacity={0.35} />
            <stop offset="100%" stopColor="hsl(var(--chart-2))" stopOpacity={0.04} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="hsl(var(--gridline))" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={24} />
        <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} width={36} />
        <Tooltip content={<ChartTooltip />} cursor={{ stroke: "hsl(var(--accent))", strokeWidth: 1 }} />
        <Area type="monotone" dataKey="count" name="New companies" stroke="hsl(var(--chart-2))" strokeWidth={2.5} fill="url(#trendFill)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
