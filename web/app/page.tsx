"use client";

import { DashboardHeader } from "@/components/dashboard-header";
import { Playlists } from "@/components/playlist";
import { SyncSummary } from "@/components/sync-summary";
import { SyncTable } from "@/components/sync-table";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Page() {
  const router = useRouter();

  useEffect(() => {
    const redirect = async (): Promise<void> => {
      const response = await api({
        method: "GET",
        service: "auth",
        path: "me",
      });

      if (!response.data || response.statusCode !== 200) {
        router.push("/login");
      }
    };

    redirect();
  }, [router]);

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
