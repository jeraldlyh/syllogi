"use client";
import { fetcher } from "@/lib/api";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SWRConfig } from "swr";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig
      value={{
        fetcher,
        revalidateOnFocus: true,
        dedupingInterval: 2000,
      }}
    >
      <TooltipProvider delayDuration={200}>{children}</TooltipProvider>
    </SWRConfig>
  );
}
