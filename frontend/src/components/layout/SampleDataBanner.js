import React, { useEffect, useState } from "react";
import { Database } from "lucide-react";
import { getHealth } from "@/lib/api";

export function SampleDataBanner() {
  const [sample, setSample] = useState(false);
  useEffect(() => {
    getHealth().then((h) => setSample(!!h.sample_mode)).catch(() => {});
  }, []);
  if (!sample) return null;
  return (
    <div
      data-testid="sample-data-banner"
      className="flex items-center justify-center gap-2 bg-accent/15 text-accent-foreground border-b border-accent/30 px-4 py-1.5 text-xs sm:text-sm"
    >
      <Database className="h-3.5 w-3.5 text-accent" />
      <span className="font-medium">Sample Data Mode</span>
      <span className="hidden sm:inline text-muted-foreground">
        — showing a labeled demo dataset. Inject DATA_GOV_API_KEY to ingest live MCA company data.
      </span>
    </div>
  );
}
