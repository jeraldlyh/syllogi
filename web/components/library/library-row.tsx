import { Text } from "@/components/common/text";
import { Badge } from "@/components/ui/badge";
import { TableCell, TableRow } from "@/components/ui/table";
import { LibraryTrack } from "@/hooks/useLibrary";
import { cn, formatClock, removeFileExtension } from "@/lib/utils";
import { ChevronRight } from "lucide-react";
import { TagComb } from "./tag-comb";

const TagCell = ({
  value,
  fallback,
  className,
}: {
  value: string;
  fallback: string;
  className: string;
}) => (
  <TableCell className={cn("max-w-0", className)}>
    <Text
      value={value || fallback}
      className={cn(
        "truncate",
        value ? "text-muted-foreground" : "text-amber-400/70",
      )}
    />
  </TableCell>
);

export const LibraryRow = ({
  track,
  onOpen,
}: {
  track: LibraryTrack;
  onOpen: (path: string) => void;
}) => (
  <TableRow
    tabIndex={0}
    role="button"
    aria-label={`Edit tags for ${track.filename}`}
    onClick={() => onOpen(track.path)}
    onKeyDown={(event) => {
      if (event.key !== "Enter" && event.key !== " ") return;

      event.preventDefault();
      onOpen(track.path);
    }}
    className="cursor-pointer focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
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
    <TagCell
      value={track.tags.artist}
      fallback="No artist"
      className="hidden sm:table-cell"
    />
    <TagCell
      value={track.tags.album}
      fallback="No album"
      className="hidden lg:table-cell"
    />
    <TableCell className="hidden md:table-cell">
      <div className="flex items-center gap-2">
        <Badge
          variant="outline"
          className="border-border font-mono text-xs uppercase tracking-wider text-muted-foreground"
        >
          {track.format}
        </Badge>
        <span className="font-mono text-xs text-muted-foreground">
          {formatClock(track.duration)}
        </span>
      </div>
    </TableCell>
    <TableCell>
      <div className="flex items-center justify-end gap-3">
        <TagComb filled={track.filled_fields} />
        <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground/50" />
      </div>
    </TableCell>
  </TableRow>
);
