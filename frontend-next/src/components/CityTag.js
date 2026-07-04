import React from "react";
import { MapPin, Layers } from "lucide-react";

export function CityTag({ city, area }) {
  if (!city) return null;
  return (
    <span className="inline-flex items-center gap-1 rounded-md border bg-chip px-2 py-0.5 text-xs text-chip-foreground">
      <MapPin className="h-3 w-3 text-accent" />
      {city}
      {area ? <span className="text-muted-foreground">· {area}</span> : null}
    </span>
  );
}

export function SectorChip({ sector }) {
  if (!sector) return null;
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-primary/8 px-2 py-0.5 text-xs text-primary dark:text-foreground dark:bg-white/5">
      <Layers className="h-3 w-3" />
      {sector}
    </span>
  );
}
