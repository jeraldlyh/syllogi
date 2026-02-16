"use client";

import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import Image from "next/image";
import { useSyncSessions } from "@/hooks/useSyncSessions";

export function DashboardHeader() {
  const { data, isError, isLoading } = useSyncSessions();

  const handleOnClick = (): void => {
    toast.success("Sync started", {
      description: "Running sync for all enabled playlists...",
    });
  };

  const formatLastSyncedTime = (date: Date): string => {
    const diff = (new Date().getTime() - date.getTime()) / 1000;
    const minutes = Math.floor(diff / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    const months = Math.floor(days / 30);
    const years = Math.floor(months / 12);

    const rtf = new Intl.RelativeTimeFormat("en-US", { numeric: "auto" });

    console.log(date);
    if (years > 0) return rtf.format(0 - years, "year");
    if (months > 0) return rtf.format(0 - months, "month");
    if (days > 0) return rtf.format(0 - days, "day");
    if (hours > 0) return rtf.format(0 - hours, "hour");
    if (minutes > 0) return rtf.format(0 - minutes, "minute");
    console.log(years, months, days, hours, minutes);
    return "just now";
  };

  if (isError || isLoading) {
    return <></>;
  }
  return (
    <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div className="flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-purple-600/20">
          <Image src="/icon.png" alt="syllogi logo" width={36} height={36} />
        </div>
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            syllogi
          </h1>
          <p className="text-xs text-muted-foreground">
            Last sync:&nbsp;
            {formatLastSyncedTime(
              new Date(data && data.length > 0 ? data[0].finished_at : ""),
            )}
          </p>
        </div>
      </div>
      <Button onClick={handleOnClick} className="gap-2">
        <RefreshCw className="h-4 w-4" />
        Run sync
      </Button>
    </header>
  );
}
