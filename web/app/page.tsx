"use client";

import { DashboardHeader } from "@/components/dashboard-header";
import { SyncSummary } from "@/components/sync-summary";
import { SyncTable } from "@/components/sync-table";

export default function Page() {
  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <DashboardHeader />
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
          <main className="flex flex-col gap-6 lg:col-span-2">
            <SyncSummary />
            <SyncTable />
          </main>
        </div>
      </div>
    </div>
  );
}
