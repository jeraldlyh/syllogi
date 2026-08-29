import { Text } from "@/components/common/text";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  LIBRARY_PAGE_SIZE,
  LibraryFilters,
  LibraryTrack,
  useLibraryTracks,
} from "@/hooks/useLibrary";
import { cn, formatClock, removeFileExtension } from "@/lib/utils";
import { ChevronRight, FileAudio, Search } from "lucide-react";
import { useState } from "react";
import { LibraryEditor } from "./library-editor";
import { TagComb } from "./tag-comb";

const ALL = "all";

const FORMAT_OPTIONS = [
  { label: "All formats", value: ALL },
  { label: "FLAC", value: "flac" },
  { label: "MP3", value: "mp3" },
  { label: "Opus", value: "opus" },
];

const MISSING_OPTIONS = [
  { label: "Everything", value: ALL },
  { label: "Missing lyrics", value: "lyrics" },
  { label: "Not linked to MusicBrainz", value: "musicbrainz_id" },
  { label: "Any tag missing", value: "any" },
];

const PLACEHOLDER_ROWS = [0, 1, 2, 3, 4, 5];

const StatDivider = () => (
  <span aria-hidden className="hidden h-3 w-px shrink-0 bg-border sm:block" />
);

const StatCount = ({
  value,
  label,
  className,
}: {
  value: number;
  label: string;
  className?: string;
}) => (
  <span className="flex shrink-0 items-baseline gap-1.5">
    <span className={cn("text-sm tabular-nums", className)}>{value}</span>
    <span className="text-muted-foreground">{label}</span>
  </span>
);

const FilterSelect = ({
  value,
  options,
  label,
  className,
  onChange,
}: {
  value: string;
  options: { label: string; value: string }[];
  label: string;
  className: string;
  onChange: (value: string) => void;
}) => (
  <Select value={value} onValueChange={onChange}>
    <SelectTrigger className={className} aria-label={label}>
      <SelectValue />
    </SelectTrigger>
    <SelectContent>
      {options.map((option) => (
        <SelectItem key={option.value} value={option.value}>
          {option.label}
        </SelectItem>
      ))}
    </SelectContent>
  </Select>
);

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

const LibraryRow = ({
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
      <p className="truncate text-sm font-medium">
        {track.tags.title || removeFileExtension(track.filename)}
      </p>
      <p className="truncate font-mono text-xs text-muted-foreground">
        {track.directory}
      </p>
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
    <TableCell className="w-px">
      <div className="flex items-center justify-end gap-3">
        <TagComb filled={track.filled_fields} />
        <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground/50" />
      </div>
    </TableCell>
  </TableRow>
);

export const Library = () => {
  const [filters, setFilters] = useState<LibraryFilters>({
    query: "",
    format: "",
    missing: "",
  });
  const [openPath, setOpenPath] = useState<string | null>(null);
  const { data, isLoading, isError, refresh } = useLibraryTracks(filters);

  const patchFilters = (patch: Partial<LibraryFilters>): void =>
    setFilters((previous) => ({ ...previous, ...patch }));

  const renderContent = (): React.JSX.Element => {
    if (isLoading && !data) {
      return (
        <div className="flex flex-col gap-2 py-2">
          {PLACEHOLDER_ROWS.map((row) => (
            <Skeleton key={row} className="h-12 w-full" />
          ))}
        </div>
      );
    }

    if (isError) {
      return (
        <div className="flex items-center justify-center py-10">
          <Text
            className="italic text-red-400"
            value="Could not read the library directory"
          />
        </div>
      );
    }

    if (!data || data.tracks.length === 0) {
      const isFiltered = Boolean(
        filters.query || filters.format || filters.missing,
      );

      return (
        <div className="flex flex-col items-center justify-center gap-2 py-14 text-center">
          <FileAudio className="h-8 w-8 text-muted-foreground/40" />
          <Text
            className="text-sm text-muted-foreground"
            value={
              isFiltered
                ? "No files match these filters"
                : "No audio files in the library yet"
            }
          />
          <Text
            className="text-xs text-muted-foreground/70"
            value={
              isFiltered
                ? "Clear the search or widen the filters to see more."
                : "Sync a playlist or download a track, then come back to tag it."
            }
          />
        </div>
      );
    }

    return (
      <>
        <div className="overflow-x-auto rounded-md border border-border">
          <Table>
            <TableHeader>
              <TableRow className="text-xs text-muted-foreground hover:bg-transparent">
                <TableHead className="sm:w-2/5">File</TableHead>
                <TableHead className="hidden sm:table-cell sm:w-1/5">
                  Artist
                </TableHead>
                <TableHead className="hidden lg:table-cell lg:w-1/5">
                  Album
                </TableHead>
                <TableHead className="hidden md:table-cell">Format</TableHead>
                <TableHead className="w-px text-right">Tags</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.tracks.map((track) => (
                <LibraryRow
                  key={track.path}
                  track={track}
                  onOpen={setOpenPath}
                />
              ))}
            </TableBody>
          </Table>
        </div>
        {data.matched > data.tracks.length && (
          <Text
            className="pt-3 text-xs text-muted-foreground"
            value={`Showing the first ${LIBRARY_PAGE_SIZE} of ${data.matched} matching files. Narrow the search to reach the rest.`}
          />
        )}
      </>
    );
  };

  return (
    <>
      <Card>
        <CardHeader className="gap-4 pb-4">
          <CardTitle className="sr-only">Library</CardTitle>
          {data ? (
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-2 border-b border-border pb-3 font-mono text-xs">
              <StatCount value={data.summary.total} label="files" />
              <StatDivider />
              <StatCount
                value={data.summary.missing_lyrics}
                label="without lyrics"
                className={cn({
                  "text-amber-400": data.summary.missing_lyrics > 0,
                  "text-primary": data.summary.missing_lyrics == 0,
                })}
              />
              <StatDivider />
              <StatCount
                value={data.summary.missing_musicbrainz_id}
                label="not linked"
                className={cn({
                  "text-amber-400": data.summary.missing_musicbrainz_id > 0,
                  "text-primary": data.summary.missing_musicbrainz_id == 0,
                })}
              />
              <StatDivider />
              <StatCount value={data.summary.lossless} label="lossless" />
              <span className="ml-auto max-w-full truncate text-muted-foreground/60">
                {data.directory.slice(0, data.directory.lastIndexOf("/") + 1)}
                <span className="text-foreground">
                  {data.directory.slice(data.directory.lastIndexOf("/") + 1)}
                </span>
              </span>
            </div>
          ) : (
            <div className="border-b border-border pb-3">
              <Skeleton className="h-4 w-72" />
            </div>
          )}
          <div className="flex flex-col gap-2 sm:flex-row">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={filters.query}
                onChange={(event) =>
                  patchFilters({ query: event.target.value })
                }
                placeholder="Search by title, artist, album or file name"
                aria-label="Search library files"
                className="pl-9"
              />
            </div>
            <FilterSelect
              value={filters.format || ALL}
              options={FORMAT_OPTIONS}
              label="Filter by format"
              className="sm:w-40"
              onChange={(value) =>
                patchFilters({
                  format:
                    value === ALL ? "" : (value as LibraryFilters["format"]),
                })
              }
            />
            <FilterSelect
              value={filters.missing || ALL}
              options={MISSING_OPTIONS}
              label="Filter by missing tags"
              className="sm:w-56"
              onChange={(value) =>
                patchFilters({
                  missing:
                    value === ALL ? "" : (value as LibraryFilters["missing"]),
                })
              }
            />
          </div>
        </CardHeader>
        <CardContent>{renderContent()}</CardContent>
      </Card>
      <LibraryEditor
        path={openPath}
        onClose={() => setOpenPath(null)}
        onSaved={refresh}
      />
    </>
  );
};
