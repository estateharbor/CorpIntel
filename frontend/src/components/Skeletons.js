import React from "react";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function CardSkeleton() {
  return (
    <Card className="p-4 space-y-3">
      <div className="flex justify-between">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
      <Skeleton className="h-3 w-32" />
      <div className="flex gap-2">
        <Skeleton className="h-5 w-20 rounded-md" />
        <Skeleton className="h-5 w-24 rounded-md" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
      </div>
    </Card>
  );
}

export function GridSkeleton({ count = 6 }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

export function KpiSkeleton() {
  return (
    <Card className="p-4 space-y-3">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-8 w-28" />
      <Skeleton className="h-3 w-32" />
    </Card>
  );
}

export function ChartSkeleton({ h = 300 }) {
  return <Skeleton className="w-full" style={{ height: h }} />;
}
