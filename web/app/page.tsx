"use client";

import { DashboardHeader } from "@/components/dashboard-header";
import { Playlists } from "@/components/playlist";
import { SyncSummary } from "@/components/sync-summary";
import { SyncTable } from "@/components/sync-table";

export default function Page() {
  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <DashboardHeader />
        <main className="mt-14 flex flex-col gap-6">
          <SyncSummary />
          <Playlists />
          <SyncTable />
        </main>
      </div>
    </div>
  );
}
