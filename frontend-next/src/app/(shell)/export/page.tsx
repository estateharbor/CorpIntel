"use client";

import ProtectedRoute from "@/components/ProtectedRoute";
import ExportPage from "@/views/Export";

export default function ExportRoute() {
  return (
    <ProtectedRoute>
      <ExportPage />
    </ProtectedRoute>
  );
}
