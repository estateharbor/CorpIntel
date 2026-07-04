import React, { useState } from "react";
import { FileText, FileSpreadsheet, FileType, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { FilterSidebar } from "@/components/FilterSidebar";
import { downloadExport } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const DEFAULT_FILTERS = { city: "All", status: "All", sector: "All", company_class: "All", date_from: "", date_to: "", min_capital: 0, max_capital: 100000000 };
const EXPORT_LIMITS = { free: 0, starter: 50, pro: -1, enterprise: -1 };

export default function ExportPage() {
  const { user, refresh } = useAuth();
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [busy, setBusy] = useState("");

  const patch = (p) => setFilters((f) => ({ ...f, ...p }));
  const reset = () => setFilters(DEFAULT_FILTERS);

  const buildBody = () => {
    const b = { limit: 5000 };
    if (filters.city !== "All") b.city = [filters.city];
    if (filters.status !== "All") b.status = filters.status;
    if (filters.sector !== "All") b.sector = [filters.sector];
    if (filters.company_class !== "All") b.company_class = filters.company_class;
    if (filters.date_from) b.date_from = filters.date_from;
    if (filters.date_to) b.date_to = filters.date_to;
    if (filters.min_capital > 0) b.min_capital = filters.min_capital;
    if (filters.max_capital < 100000000) b.max_capital = filters.max_capital;
    return b;
  };

  const doExport = async (format) => {
    setBusy(format);
    try {
      await downloadExport(format, buildBody());
      toast.success(`${format.toUpperCase()} exported`);
      await refresh();
    } catch (err) {
      const detail = err?.response?.data?.detail || "Export failed";
      toast.error(typeof detail === "string" ? detail : "Export failed");
    } finally {
      setBusy("");
    }
  };

  const limit = EXPORT_LIMITS[user?.plan || "free"];
  const used = user?.exports_used || 0;
  const unlimited = limit === -1;
  const pct = unlimited ? 100 : limit === 0 ? 0 : Math.min(100, (used / limit) * 100);

  const FORMATS = [
    { id: "csv", label: "CSV", desc: "All fields, comma-separated", icon: FileText, testid: "export-format-csv" },
    { id: "excel", label: "Excel", desc: "Formatted, one sheet per city", icon: FileSpreadsheet, testid: "export-format-excel" },
    { id: "pdf", label: "PDF Report", desc: "Summary with charts & top companies", icon: FileType, testid: "export-format-pdf" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold">Export</h1>
        <p className="text-sm text-muted-foreground">Download filtered company intelligence in your preferred format</p>
      </div>

      <Card className="p-5" data-testid="export-usage-meter">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Exports this month</span>
          <span className="text-sm text-muted-foreground tabular-nums">
            {unlimited ? `${used} · Unlimited` : `${used} / ${limit}`}
          </span>
        </div>
        <Progress value={pct} />
        {limit === 0 && <p className="mt-2 text-xs text-destructive">Your Free plan does not include exports. Upgrade to Starter or Pro.</p>}
      </Card>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="p-4 lg:col-span-1">
          <FilterSidebar value={filters} onChange={patch} onReset={reset} />
        </Card>

        <div className="lg:col-span-2 grid sm:grid-cols-1 gap-4">
          {FORMATS.map((f) => {
            const Icon = f.icon;
            return (
              <Card key={f.id} className="p-4 xs:p-5 flex flex-col items-start justify-between gap-4 xs:flex-row xs:items-center">
                <div className="flex items-center gap-4">
                  <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary dark:bg-white/5 dark:text-foreground">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="font-heading font-semibold">{f.label}</div>
                    <div className="text-sm text-muted-foreground">{f.desc}</div>
                  </div>
                </div>
                <Button className="w-full xs:w-auto" onClick={() => doExport(f.id)} disabled={!!busy || limit === 0} data-testid={f.testid}>
                  {busy === f.id ? <Loader2 className="h-4 w-4 animate-spin" /> : "Download"}
                </Button>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
