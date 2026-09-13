import { Skeleton } from "@/components/ui/skeleton";
import React from "react";

export const ChartArtistSkeleton = (): React.JSX.Element => {
  return (
    <div className="relative px-4 py-6 md:px-6">
      <div className="flex flex-col gap-6 md:flex-row md:items-end">
        <Skeleton className="h-40 w-40 shrink-0 rounded-2xl md:h-56 md:w-56" />
        <div className="flex flex-1 flex-col gap-3 pb-1">
          <Skeleton className="h-12 w-3/4 md:h-16" />
          <Skeleton className="h-4 w-1/2" />
          <div className="flex gap-2">
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-6 w-24 rounded-full" />
            <Skeleton className="h-6 w-16 rounded-full" />
          </div>
        </div>
      </div>
      <div className="mt-10">
        <Skeleton className="h-4 w-28" />
        <div className="mt-4 flex gap-3 overflow-hidden">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton
              key={i}
              className="h-36 w-36 shrink-0 rounded-xl md:h-40 md:w-40"
            />
          ))}
        </div>
      </div>
      <div className="mt-10">
        <Skeleton className="h-4 w-28" />
        <div className="mt-4 space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-10 w-10 rounded-md" />
              <Skeleton className="h-4 flex-1" />
              <Skeleton className="h-4 w-12" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
