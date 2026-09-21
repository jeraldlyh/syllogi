import { TrackFormatBadge } from "@/components/common/track-format-badge";
import { Text } from "@/components/common/text";
import { Badge } from "@/components/ui/badge";
import { TableCell, TableRow } from "@/components/ui/table";
import { LibraryTrack } from "@/hooks/useLibrary";
import {
  cn,
  formatClock,
  formatDateTime,
  removeFileExtension,
} from "@/lib/utils";
import { ChevronRight } from "lucide-react";
import { TagComb } from "./tag-comb";

const TagText = ({
  value,
  fallback,
  emphasis,
}: {
  value: string;
  fallback: string;
  emphasis?: "artist" | "album";
}) => (
  <Text
    value={value || fallback}
    className={cn(
      "truncate",
      !value && "text-amber-400/70",
      value && emphasis === "artist" && "font-medium text-foreground",
      value && emphasis === "album" && "italic text-muted-foreground",
      value && !emphasis && "text-muted-foreground",
    )}
  />
);

export const LibraryRow = ({
  track,
  onOpen,
}: {
  track: LibraryTrack;
  onOpen: (path: string) => void;
}) => {
  const incomplete = !track.tags.artist || !track.tags.album;

  return (
    <TableRow
      tabIndex={0}
      role="button"
      onClick={() => onOpen(track.path)}
      onKeyDown={(event) => {
        if (event.key !== "Enter" && event.key !== " ") return;

        event.preventDefault();
        onOpen(track.path);
      }}
      className={cn(
        "cursor-pointer focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
        incomplete && "bg-amber-500/5 hover:bg-amber-500/10",
      )}
    >
      <TableCell className="max-w-0">
        <Text
          variant="sm"
          className="truncate font-medium"
          value={track.tags.title || removeFileExtension(track.filename)}
        />
        <Text
          disableViewport
          mono
          muted
          className="truncate"
          value={track.directory}
        />
      </TableCell>
      <TableCell className="hidden md:table-cell max-w-0">
        <TagText
          value={track.tags.artist}
          fallback="No artist"
          emphasis="artist"
        />
        <TagText
          value={track.tags.album}
          fallback="No album"
          emphasis="album"
        />
      </TableCell>
      <TableCell className="hidden md:table-cell">
        <div className="flex flex-col items-center gap-2">
          <TrackFormatBadge format={track.format} />
          <Badge
            className="border-border font-mono text-xs uppercase tracking-wider text-muted-foreground"
            variant="outline"
          >
            {formatClock(track.duration)}
          </Badge>
        </div>
      </TableCell>
      <TableCell className="hidden md:table-cell">
        <Text
          mono
          muted
          className="text-xs"
          value={
            track.mtime
              ? formatDateTime(new Date(track.mtime * 1000).toISOString())
              : ""
          }
        />
      </TableCell>
      <TableCell>
        <div className="flex items-center justify-end gap-3">
          <TagComb filled={track.filled_fields} />
          <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground/50" />
        </div>
      </TableCell>
    </TableRow>
  );
};
