"use client";

import { Text } from "@/components/common/text";
import { DashboardHeader } from "@/components/dashboard-header";
import { Playlists } from "@/components/playlist";
import { SyncSummary } from "@/components/sync-summary";
import { SyncTable } from "@/components/sync-table";
import { api } from "@/lib/api";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

export default function Page() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const timerRef = useRef<NodeJS.Timeout | undefined>(undefined);

  useEffect(() => {
    const startTimer = (): void => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      const newTimer = setTimeout(() => setLoading(false), 10000);
      timerRef.current = newTimer;
    };

    startTimer();

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

      clearTimeout(timerRef.current);
      timerRef.current = undefined;
      setLoading(false);
    };

    redirect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  return (
    <div className="min-h-screen bg-background">
      {loading ? (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-6 bg-background">
          <div className="relative flex items-center justify-center">
            <span className="absolute inline-flex h-32 w-32 animate-ping rounded-full bg-primary opacity-20" />
            <svg
              className="h-20 w-20 animate-spin"
              viewBox="0 0 64 64"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <circle
                cx="32"
                cy="32"
                r="28"
                stroke="currentColor"
                strokeWidth="4"
                className="text-border"
              />
              <path
                d="M32 4 A28 28 0 0 1 60 32"
                stroke="currentColor"
                strokeWidth="4"
                strokeLinecap="round"
                className="text-primary"
              />
            </svg>
            <Image
              src="/icon.png"
              alt="syllogi logo"
              fill
              className="absolute p-6"
            />
          </div>
          <div className="flex flex-col items-center gap-1">
            <Text value="Signing you in" className="text-lg" />
            <Text
              value="Please wait a moment..."
              className="text-sm text-muted-foreground"
            />
          </div>
        </div>
      ) : (
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <DashboardHeader />
          <main className="mt-14 flex flex-col gap-6">
            <SyncSummary />
            <Playlists />
            <SyncTable />
          </main>
        </div>
      )}
    </div>
  );
}
