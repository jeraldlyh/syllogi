"use client";

import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import Image from "next/image";

export function DashboardHeader() {
  const handleOnClick = (): void => {
    toast.success("Sync started", {
      description: "Running sync for all enabled playlists...",
    });
  };

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
            Last sync: 3 minutes ago
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
