"use client";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { api } from "@/lib/api";
import { Dot, LogOut } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { useMe } from "@/hooks/useMe";
import { useSlskdHealth } from "@/hooks/useSlskdHealth";
import { useSyncSessions } from "@/hooks/useSyncSessions";
import { cn } from "@/lib/utils";

export function DashboardHeader() {
  const router = useRouter();
  const { data, isError, isLoading } = useSyncSessions();
  const { data: currentUser } = useMe();
  const { data: slskdHealth } = useSlskdHealth();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const formatLastSyncedTime = (date: Date): string => {
    const diff = (new Date().getTime() - date.getTime()) / 1000;
    const minutes = Math.floor(diff / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    const months = Math.floor(days / 30);
    const years = Math.floor(months / 12);

    const rtf = new Intl.RelativeTimeFormat("en-US", { numeric: "auto" });

    if (years > 0) return rtf.format(0 - years, "year");
    if (months > 0) return rtf.format(0 - months, "month");
    if (days > 0) return rtf.format(0 - days, "day");
    if (hours > 0) return rtf.format(0 - hours, "hour");
    if (minutes > 0) return rtf.format(0 - minutes, "minute");

    return "just now";
  };

  const handleLogout = async (): Promise<void> => {
    if (isLoggingOut) return;

    setIsLoggingOut(true);

    const toastId = toast.loading("Logging out...");

    try {
      const response = await api({
        method: "POST",
        service: "auth",
        path: "logout",
      });

      if (response.statusCode === 200 || response.statusCode === 401) {
        toast.success("Logged out", { id: toastId });
        router.replace("/login");
        return;
      }

      toast.error("Logout failed", {
        description: response.error?.message || "An unknown error occurred",
        id: toastId,
      });
    } catch {
      toast.error("Logout failed", {
        description: "Unable to reach the server right now.",
        id: toastId,
      });
    } finally {
      setIsLoggingOut(false);
    }
  };

  if (isError || isLoading) {
    return <></>;
  }

  return (
    <header className="flex gap-4 items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-purple-600/20">
          <Image
            src="/icon.png"
            alt="syllogi logo"
            fill
            className="p-2.5 object-contain"
          />
        </div>
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            syllogi
          </h1>
          <p className="text-xs text-muted-foreground">
            Last sync&nbsp;
            {formatLastSyncedTime(
              new Date(data && data.length > 0 ? data[0].finished_at : ""),
            )}
          </p>
          {slskdHealth?.configured && (
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="relative w-fit flex mt-1 items-center justify-center p-1">
                  <Image
                    src="/slskd.svg"
                    alt="slskd"
                    width={18}
                    height={18}
                    className={cn(
                      "shrink-0 transition-all",
                      !slskdHealth.connected && "opacity-40 grayscale",
                    )}
                  />
                  <span
                    className={cn(
                      "absolute animate-pulse -bottom-0.5 -right-0.5 block h-2 w-2 rounded-full ring-2 ring-background",
                      slskdHealth.connected ? "bg-emerald-500" : "bg-red-500",
                    )}
                  />
                </div>
              </TooltipTrigger>
              <TooltipContent>
                {slskdHealth.connected
                  ? "slskd is connected"
                  : "slskd is not reachable"}
              </TooltipContent>
            </Tooltip>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2 self-start md:self-auto">
        {currentUser?.username && (
          <p className="text-sm font-medium border-b border-border text-muted-foreground">
            {currentUser.username}
          </p>
        )}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              disabled={isLoggingOut}
              aria-label="Log out"
              className="text-muted-foreground hover:text-foreground hover:bg-destructive"
            >
              <LogOut
                className={cn({
                  "animate-spin": isLoggingOut,
                })}
              />
              <span className="sr-only">Logout</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent>Log out</TooltipContent>
        </Tooltip>
      </div>
    </header>
  );
}
