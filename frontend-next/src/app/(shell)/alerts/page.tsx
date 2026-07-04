"use client";

import ProtectedRoute from "@/components/ProtectedRoute";
import Alerts from "@/views/Alerts";

export default function AlertsPage() {
  return (
    <ProtectedRoute>
      <Alerts />
    </ProtectedRoute>
  );
}
