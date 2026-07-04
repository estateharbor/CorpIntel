"use client";

import ProtectedRoute from "@/components/ProtectedRoute";
import AdminEnrichment from "@/views/AdminEnrichment";

export default function AdminEnrichmentPage() {
  return (
    <ProtectedRoute>
      <AdminEnrichment />
    </ProtectedRoute>
  );
}
