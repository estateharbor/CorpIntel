import React from "react";
import { useQuery } from "@tanstack/react-query";
import { RotateCcw } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { getSectors } from "@/lib/api";
import { CITIES, STATUSES, CLASSES, formatINR } from "@/lib/format";

const CAP_MAX = 100000000; // 10 Cr

export function FilterSidebar({ value, onChange, onReset }) {
  const { data: sectorsData } = useQuery({ queryKey: ["sectors-filter"], queryFn: () => getSectors("All", 30) });
  const sectorOptions = (sectorsData?.sectors || []).map((s) => s.sector).filter(Boolean);
  const cap = [value.min_capital ?? 0, value.max_capital ?? CAP_MAX];

  return (
    <div className="space-y-5" data-testid="search-filter-sidebar">
      <div className="flex items-center justify-between">
        <h3 className="font-heading text-sm font-semibold">Filters</h3>
        <Button variant="ghost" size="sm" className="h-8 text-xs" onClick={onReset} data-testid="search-filter-reset">
          <RotateCcw className="mr-1 h-3.5 w-3.5" /> Reset
        </Button>
      </div>

      <div className="space-y-2">
        <Label className="text-xs text-muted-foreground">City</Label>
        <Select value={value.city || "All"} onValueChange={(v) => onChange({ city: v })}>
          <SelectTrigger className="h-9" data-testid="search-filter-city-select"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="All">All cities</SelectItem>
            {CITIES.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label className="text-xs text-muted-foreground">Status</Label>
        <Select value={value.status || "All"} onValueChange={(v) => onChange({ status: v })}>
          <SelectTrigger className="h-9" data-testid="search-filter-status-select"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="All">All statuses</SelectItem>
            {STATUSES.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label className="text-xs text-muted-foreground">Sector</Label>
        <Select value={value.sector || "All"} onValueChange={(v) => onChange({ sector: v })}>
          <SelectTrigger className="h-9" data-testid="search-filter-sector-select"><SelectValue placeholder="All sectors" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="All">All sectors</SelectItem>
            {sectorOptions.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label className="text-xs text-muted-foreground">Company class</Label>
        <Select value={value.company_class || "All"} onValueChange={(v) => onChange({ company_class: v })}>
          <SelectTrigger className="h-9" data-testid="search-filter-class-select"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="All">All classes</SelectItem>
            {CLASSES.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label className="text-xs text-muted-foreground">Incorporation date</Label>
        <div className="grid grid-cols-2 gap-2">
          <Input type="date" className="h-9" value={value.date_from || ""} onChange={(e) => onChange({ date_from: e.target.value })} data-testid="search-filter-date-from" />
          <Input type="date" className="h-9" value={value.date_to || ""} onChange={(e) => onChange({ date_to: e.target.value })} data-testid="search-filter-date-to" />
        </div>
      </div>

      <div className="space-y-3">
        <Label className="text-xs text-muted-foreground">Paid-up capital</Label>
        <Slider
          min={0}
          max={CAP_MAX}
          step={500000}
          value={cap}
          onValueChange={(v) => onChange({ min_capital: v[0], max_capital: v[1] })}
          data-testid="search-filter-capital-slider"
        />
        <div className="flex justify-between text-xs text-muted-foreground tabular-nums">
          <span>{formatINR(cap[0])}</span>
          <span>{cap[1] >= CAP_MAX ? "₹10 Cr+" : formatINR(cap[1])}</span>
        </div>
      </div>
    </div>
  );
}
