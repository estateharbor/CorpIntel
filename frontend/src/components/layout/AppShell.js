import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { SampleDataBanner } from "@/components/layout/SampleDataBanner";

export default function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  return (
    <div className="min-h-screen bg-background">
      <SampleDataBanner />
      <div className="flex">
        {/* Desktop sidebar */}
        <aside className="hidden lg:flex w-[272px] shrink-0 h-[calc(100vh)] sticky top-0">
          <Sidebar />
        </aside>

        {/* Mobile sidebar */}
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetContent side="left" className="p-0 w-[272px] border-r-0">
            <Sidebar onNavigate={() => setMobileOpen(false)} />
          </SheetContent>
        </Sheet>

        <div className="flex-1 min-w-0 flex flex-col min-h-screen">
          <Topbar onMenuClick={() => setMobileOpen(true)} />
          <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6">
            <div className="mx-auto w-full max-w-[1400px]">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
