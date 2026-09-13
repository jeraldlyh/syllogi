import { Text } from "@/components/common/text";
import { Disc3 } from "lucide-react";
import React from "react";

export const ChartArtistEmptyState = ({
  title,
  description,
}: {
  title: string;
  description: string;
}): React.JSX.Element => {
  return (
    <div className="flex mt-6 flex-1 flex-col items-center justify-center px-6 pb-8">
      <div className="flex max-w-sm flex-col items-center gap-4 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full border border-white/10 bg-white/[0.03]">
          <Disc3 className="size-6 text-muted-foreground" />
        </div>
        <h1 className="text-2xl font-bold">{title}</h1>
        <Text variant="sm" muted value={description} />
      </div>
    </div>
  );
};
