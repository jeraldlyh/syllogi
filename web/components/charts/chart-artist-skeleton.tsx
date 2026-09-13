import { Skeleton } from "@/components/ui/skeleton";
import React from "react";

export const ChartArtistSkeleton = (): React.JSX.Element => {
  return (
    <div className="relative flex flex-col gap-8 px-4 py-6 md:px-6">
      <div className="flex flex-col gap-6 md:flex-row">
        <Skeleton className="aspect-square w-full shrink-0 rounded-2xl md:h-56 md:w-56" />
        <div className="flex flex-1 flex-col justify-center">
          <Skeleton className="h-12 w-3/4 md:h-16" />
          <div className="mt-2 flex gap-2">
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-6 w-24 rounded-full" />
            <Skeleton className="h-6 w-16 rounded-full" />
          </div>
          <div className="md:mt-auto mt-2">
            <Skeleton className="h-4 w-1/2" />
          </div>
        </div>
      </div>
      <div>
        <Skeleton className="h-4 w-28" />
        <div className="mt-3 flex flex-wrap gap-1.5">
          <Skeleton className="h-6 w-14 rounded-full" />
          <Skeleton className="h-6 w-16 rounded-full" />
          <Skeleton className="h-6 w-14 rounded-full" />
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
        <div className="mt-4 flex gap-3 overflow-hidden">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="w-36 shrink-0 md:w-40">
              <Skeleton className="aspect-square w-full rounded-xl" />
              <Skeleton className="mt-2 h-4 w-4/5" />
              <Skeleton className="mt-1.5 h-4 w-3/5" />
            </div>
          ))}
        </div>
      </div>
      <div>
        <Skeleton className="h-4 w-28" />
        <div className="mt-4 space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-10 w-10 rounded-md" />
              <Skeleton className="h-4 flex-1" />
              <Skeleton className="h-8 w-20 rounded-md" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
