import { Text } from "@/components/common/text";
import { Button } from "@/components/ui/button";
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
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  LIBRARY_PAGE_SIZE,
  LibraryFilters,
  rescanLibrary,
  useLibraryTracks,
} from "@/hooks/useLibrary";
import { cn } from "@/lib/utils";
import { FileAudio, Loader2, RefreshCw, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { LibraryEditor } from "./library-editor";
import { LibraryPagination } from "./library-pagination";
import { LibraryRow } from "./library-row";

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
  <span aria-hidden className="hidden h-3 w-px shrink-0 bg-border md:block" />
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

export const Library = () => {
  const [filters, setFilters] = useState<LibraryFilters>({
    query: "",
    format: "",
    missing: "",
  });
  const [openPath, setOpenPath] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const { data, isLoading, isError, refresh } = useLibraryTracks(filters, page);
  const FilterActivityIcon = isLoading ? Loader2 : Search;

  useEffect(() => {
    if (!data) return;

    const lastPage = Math.max(
      0,
      Math.ceil(data.matched / LIBRARY_PAGE_SIZE) - 1,
    );

    if (page > lastPage) setPage(lastPage);
  }, [data, page]);

  const patchFilters = (patch: Partial<LibraryFilters>): void => {
    setPage(0);
    setFilters((previous) => ({ ...previous, ...patch }));
  };

  const handleRescan = async (): Promise<void> => {
    await rescanLibrary();
    await refresh();
  };

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

      if (data?.scanning && !isFiltered) {
        return (
          <div className="flex flex-col items-center justify-center gap-2 py-14 text-center">
            <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground/40" />
            <Text variant="sm" muted value="Scanning the library" />
            <Text
              className="text-muted-foreground/70"
              value="Files appear as they are read. This takes a while the first time."
            />
          </div>
        );
      }

      return (
        <div className="flex flex-col items-center justify-center gap-2 py-14 text-center">
          <FileAudio className="h-8 w-8 text-muted-foreground/40" />
          <Text
            variant="sm"
            muted
            value={
              isFiltered
                ? "No files match these filters"
                : "No audio files in the library yet"
            }
          />
          <Text
            className="text-muted-foreground/70"
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
        <div
          className={cn(
            "overflow-x-auto rounded-md border border-border transition-opacity md:max-h-[75vh] max-h-[50vh]",
            isLoading && "opacity-50",
          )}
        >
          <Table>
            <TableHeader>
              <TableRow className="text-xs text-muted-foreground hover:bg-transparent">
                <TableHead className="md:w-2/5">File</TableHead>
                <TableHead className="hidden md:table-cell md:w-1/5">
                  Artist
                </TableHead>
                <TableHead className="hidden lg:table-cell lg:w-1/5">
                  Album
                </TableHead>
                <TableHead className="hidden md:table-cell">Format</TableHead>
                <TableHead className="text-right md:text-start w-px">
                  Tags
                </TableHead>
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
        <LibraryPagination
          page={page}
          shown={data.tracks.length}
          matched={data.matched}
          onChange={setPage}
        />
      </>
    );
  };

  return (
    <>
      <Card>
        <CardHeader className="gap-4 pb-4">
          <CardTitle className="sr-only">Library</CardTitle>
          {data ? (
            <div className="border-b border-border pb-3 font-mono text-xs">
              <div className="md:hidden block">
                <Text
                  muted
                  className="uppercase tracking-widest pb-2"
                  value="Directory"
                />
                <p className="truncate">
                  <span className="text-muted-foreground/60">
                    {data.directory.slice(
                      0,
                      data.directory.lastIndexOf("/") + 1,
                    )}
                  </span>
                  {data.directory.slice(data.directory.lastIndexOf("/") + 1)}
                </p>
                <Text
                  muted
                  className="uppercase tracking-widest pb-2 mt-4"
                  value="Statistics"
                />
              </div>
              <div className="grid grid-cols-2 items-baseline gap-x-4 gap-y-2 md:flex md:flex-wrap md:gap-x-3">
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
                <StatCount
                  value={data.summary.duplicates}
                  label="duplicated"
                  className={cn({
                    "text-amber-400": data.summary.duplicates > 0,
                    "text-primary": data.summary.duplicates == 0,
                  })}
                />
                <StatDivider />
                <StatCount
                  value={data.summary.empty_directories}
                  label="empty folders"
                  className={cn({
                    "text-amber-400": data.summary.empty_directories > 0,
                    "text-primary": data.summary.empty_directories == 0,
                  })}
                />
                <StatDivider />
                <StatCount value={data.summary.lossless} label="lossless" />
                {data.scanning && (
                  <>
                    <StatDivider />
                    <span className="flex shrink-0 items-center gap-1.5 text-primary">
                      <RefreshCw className="h-3 w-3 animate-spin" />
                      <span>scanning</span>
                    </span>
                  </>
                )}
                <span className="hidden min-w-0 max-w-full truncate text-muted-foreground/60 md:ml-auto md:inline">
                  {data.directory.slice(0, data.directory.lastIndexOf("/") + 1)}
                  <span className="text-foreground">
                    {data.directory.slice(data.directory.lastIndexOf("/") + 1)}
                  </span>
                </span>
              </div>
            </div>
          ) : (
            <div className="border-b border-border pb-3">
              <Skeleton className="h-4 w-full md:w-72" />
              <Skeleton className="mt-2 h-4 w-full md:hidden" />
              <Skeleton className="mt-2 h-4 w-1/3 md:hidden" />
            </div>
          )}
          <div className="flex flex-col gap-2 md:flex-row">
            <div className="relative flex-1">
              <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2">
                <FilterActivityIcon
                  className={cn(
                    "h-4 w-4 text-muted-foreground",
                    isLoading && "animate-spin text-primary",
                  )}
                />
              </span>
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
              className="md:w-40"
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
              className="md:w-56"
              onChange={(value) =>
                patchFilters({
                  missing:
                    value === ALL ? "" : (value as LibraryFilters["missing"]),
                })
              }
            />
            <Button
              variant="outline"
              size="icon"
              onClick={handleRescan}
              disabled={data?.scanning}
              aria-label="Rescan the library"
              title="Rescan the library"
              className="shrink-0"
            >
              <RefreshCw className={cn(data?.scanning && "animate-spin")} />
            </Button>
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
