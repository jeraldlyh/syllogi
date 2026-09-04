import { Text } from "@/components/common/text";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { LibraryTrack } from "@/hooks/useLibrary";
import { cn, formatClock, formatSize } from "@/lib/utils";
import { useId } from "react";

interface IProps {
  track: LibraryTrack;
  isSelected: boolean;
  isOnlyCopyLeft: boolean;
  onToggle: () => void;
}

export const LibraryDuplicateRow = ({
  track,
  isSelected,
  isOnlyCopyLeft,
  onToggle,
}: IProps) => {
  const id = useId();

  return (
    <li
      className={cn(
        "flex items-center gap-3 border-b border-border px-3 py-2 last:border-b-0",
        isSelected && "bg-destructive/10",
      )}
    >
      <Checkbox
        id={id}
        checked={isSelected}
        disabled={isOnlyCopyLeft}
        onCheckedChange={onToggle}
      />
      <label
        htmlFor={id}
        className={cn(
          "flex flex-1 cursor-pointer items-center",
          isOnlyCopyLeft && "cursor-not-allowed",
        )}
      >
        <div className="flex-1">
          <Text
            disableViewport
            mono
            className={cn("truncate", isSelected && "line-through opacity-60")}
            value={track.filename}
          />
          <Text
            disableViewport
            mono
            muted
            className="truncate"
            value={track.directory}
          />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-x-2 place-items-center">
          <Badge
            variant="outline"
            className="border-border font-mono uppercase text-muted-foreground"
          >
            {track.format}
          </Badge>
          <Text
            disableViewport
            mono
            muted
            className="hidden sm:inline"
            value={formatSize(track.size)}
          />
          <Text
            disableViewport
            mono
            muted
            value={formatClock(track.duration)}
          />
        </div>
      </label>
    </li>
  );
};
