"use client";
import { StatusBadge } from "@/components/common/status-badge";
import { Text } from "@/components/common/text";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  RecommendationSession,
  useRecommendationSessions,
} from "@/hooks/useRecommendationSessions";
import {
  capitaliseFirstLetter,
  cn,
  formatDateTime,
  formatDuration,
} from "@/lib/utils";
import { RefreshCw, Search } from "lucide-react";
import { useState } from "react";
import { SortDirection, SortIcon } from "../common/sort-icon";
import { RecommendationStrategyBadge } from "./recommendation-strategy-badge";

type SortColumn =
  | "time"
  | "user"
  | "strategy"
  | "requested"
  | "matched"
  | "missing"
  | "duration"
  | "status"
  | null;

export const RecommendationTable = () => {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedSession, setSelectedSession] =
    useState<RecommendationSession | null>(null);
  const [sortColumn, setSortColumn] = useState<SortColumn>("time");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  const {
    data,
    isError,
    isLoading,
    mutate: fetchRecommendationSessions,
  } = useRecommendationSessions();

  const getFilteredSessions = (): RecommendationSession[] => {
    if (isError || isLoading || !data) return [];

    return data.filter((session) => {
      const matchesSearch =
        session.username.toLowerCase().includes(search.toLowerCase()) ||
        session.strategy.toLowerCase().includes(search.toLowerCase());

      const matchesStatus =
        statusFilter === "all" || session.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  };

  const handleSort = (column: typeof sortColumn): void => {
    if (sortColumn !== column) {
      setSortColumn(column);
      setSortDirection(column === "time" ? "desc" : "asc");
      return;
    }

    if (sortDirection === "asc") {
      setSortDirection("desc");
    } else if (sortDirection === "desc") {
      setSortDirection(null);
      setSortColumn(null);
    } else {
      setSortDirection("asc");
    }
  };

  const getSortedSessions = (): RecommendationSession[] => {
    const filtered = getFilteredSessions();

    if (!sortColumn || !sortDirection) return filtered;

    const multiplier = sortDirection === "asc" ? 1 : -1;

    return [...filtered].sort((a, b) => {
      switch (sortColumn) {
        case "time":
          return (
            multiplier *
            (new Date(a.finished_at).getTime() -
              new Date(b.finished_at).getTime())
          );
        case "user":
          return multiplier * a.username.localeCompare(b.username);
        case "strategy":
          return multiplier * a.strategy.localeCompare(b.strategy);
        case "requested":
          return multiplier * (a.requested_count - b.requested_count);
        case "matched":
          return (
            multiplier * (a.matched_tracks.length - b.matched_tracks.length)
          );
        case "missing":
          return (
            multiplier * (a.missing_tracks.length - b.missing_tracks.length)
          );
        case "duration":
          return multiplier * (a.duration_seconds - b.duration_seconds);
        case "status":
          return multiplier * a.status.localeCompare(b.status);
        default:
          return 0;
      }
    });
  };

  const renderTableHeader = (): React.JSX.Element => {
    return (
      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by username or strategy..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
            disabled={isLoading || isError}
          />
        </div>
        <Select
          value={statusFilter}
          onValueChange={setStatusFilter}
          disabled={isLoading || isError}
        >
          <SelectTrigger className="w-full sm:w-[160px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
      </div>
    );
  };

  const renderDialogContent = (): React.JSX.Element | null => {
    if (!selectedSession) return null;

    if (selectedSession.status === "failed") {
      return (
        <DialogContent className="max-w-lg bg-card">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Text
                value="Recommendation Failed"
                className="text-lg font-semibold"
              />
              <StatusBadge status={selectedSession.status} />
            </DialogTitle>
          </DialogHeader>
          <div className="p-4 bg-red-500/5 rounded-md text-red-400">
            <Text value="Stacktrace:" className="text-sm" />
            <ScrollArea className="max-h-64 mt-2 rounded-md border bg-secondary/50 p-2 overflow-y-scroll">
              <pre className="text-xs text-wrap">
                {selectedSession.error_message || "No stacktrace available."}
              </pre>
            </ScrollArea>
          </div>
        </DialogContent>
      );
    }

    return (
      <DialogContent className="max-w-lg bg-card">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Text
              value={selectedSession.username}
              className="text-lg font-semibold"
            />
            <StatusBadge status={selectedSession.status} />
          </DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <DialogItem
            label="Provider"
            value={capitaliseFirstLetter(selectedSession.provider)}
          />
          <DialogItem
            label="Strategy"
            value={capitaliseFirstLetter(
              selectedSession.strategy.replaceAll("_", " "),
            )}
          />
          <DialogItem
            label="Requested"
            value={String(selectedSession.requested_count)}
          />
          <DialogItem
            label="Generated"
            value={String(selectedSession.generated_count)}
          />
          <DialogItem
            label="Duration"
            value={formatDuration(selectedSession.duration_seconds)}
          />
          <DialogItem
            label="Finished At"
            value={formatDateTime(selectedSession.finished_at)}
          />
        </div>

        <div className="mt-2 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TrackList
            title={`Matched tracks (${selectedSession.matched_tracks.length})`}
            tracks={selectedSession.matched_tracks}
            accent="text-emerald-400"
          />
          <TrackList
            title={`Missing tracks (${selectedSession.missing_tracks.length})`}
            tracks={selectedSession.missing_tracks}
            accent="text-amber-400"
          />
        </div>
      </DialogContent>
    );
  };

  const renderTable = (): React.JSX.Element => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-6">
          <Text muted className="italic" value="Loading..." />
        </div>
      );
    }

    if (isError) {
      return (
        <div className="flex items-center justify-center py-6">
          <Text
            muted
            className="italic text-red-400"
            value="Failed to load recommendation sessions"
          />
        </div>
      );
    }

    const sortedSessions = getSortedSessions();

    if (sortedSessions.length === 0) {
      return (
        <div className="flex items-center justify-center py-6">
          <Text
            muted
            className="italic"
            value={
              data && data.length === 0
                ? "Run your first recommendation"
                : "No sessions match your filters"
            }
          />
        </div>
      );
    }

    return (
      <div className="overflow-x-auto rounded-md border border-border max-h-96">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent text-xs text-muted-foreground">
              <TableHead className="cursor-pointer select-none">
                <button
                  className="flex items-center"
                  onClick={() => handleSort("time")}
                >
                  Time
                  <SortIcon
                    column="time"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                  />
                </button>
              </TableHead>
              <TableHead className="cursor-pointer select-none">
                <button
                  className="flex items-center"
                  onClick={() => handleSort("user")}
                >
                  User
                  <SortIcon
                    column="user"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                  />
                </button>
              </TableHead>
              <TableHead className="hidden sm:table-cell cursor-pointer select-none">
                <button
                  className="flex items-center"
                  onClick={() => handleSort("user")}
                >
                  Strategy
                  <SortIcon
                    column="strategy"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                  />
                </button>
              </TableHead>
              <TableHead className="hidden md:table-cell cursor-pointer select-none">
                <button
                  className="flex items-center"
                  onClick={() => handleSort("requested")}
                >
                  Requested
                  <SortIcon
                    column="requested"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                  />
                </button>
              </TableHead>
              <TableHead className="hidden md:table-cell cursor-pointer select-none">
                <button
                  className="flex items-center"
                  onClick={() => handleSort("matched")}
                >
                  Matched
                  <SortIcon
                    column="matched"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                  />
                </button>
              </TableHead>
              <TableHead className="hidden lg:table-cell cursor-pointer select-none">
                <button
                  className="flex items-center"
                  onClick={() => handleSort("missing")}
                >
                  Missing
                  <SortIcon
                    column="missing"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                  />
                </button>
              </TableHead>
              <TableHead className="hidden lg:table-cell cursor-pointer select-none">
                <button
                  className="flex items-center"
                  onClick={() => handleSort("duration")}
                >
                  Duration
                  <SortIcon
                    column="duration"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                  />
                </button>
              </TableHead>
              <TableHead className="cursor-pointer select-none">
                <button
                  className="flex items-center"
                  onClick={() => handleSort("status")}
                >
                  Status
                  <SortIcon
                    column="status"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                  />
                </button>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedSessions.map((session) => (
              <TableRow
                key={session.id}
                className="cursor-pointer transition-colors hover:bg-secondary/50"
                onClick={() => setSelectedSession(session)}
              >
                <TableCell>
                  <Text muted value={formatDateTime(session.finished_at)} />
                </TableCell>
                <TableCell>
                  <Text value={session.username} />
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  <RecommendationStrategyBadge strategy={session.strategy} />
                </TableCell>
                <TableCell className="hidden md:table-cell">
                  <Text muted value={String(session.requested_count)} />
                </TableCell>
                <TableCell className="hidden md:table-cell text-emerald-400">
                  <Text value={String(session.matched_tracks.length)} />
                </TableCell>
                <TableCell className="hidden lg:table-cell text-amber-400">
                  <Text value={String(session.missing_tracks.length)} />
                </TableCell>
                <TableCell className="hidden lg:table-cell">
                  <Text
                    muted
                    value={formatDuration(session.duration_seconds)}
                  />
                </TableCell>
                <TableCell>
                  <StatusBadge status={session.status} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  };

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base font-medium text-foreground">
            Recent Sessions
          </CardTitle>
          <Button size="sm" onClick={() => fetchRecommendationSessions()}>
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </CardHeader>
        <CardContent>
          {renderTableHeader()}
          {renderTable()}
        </CardContent>
      </Card>

      <Dialog
        open={selectedSession !== null}
        onOpenChange={(open) => !open && setSelectedSession(null)}
      >
        {renderDialogContent()}
      </Dialog>
    </>
  );
};

const DialogItem = ({ label, value }: { label: string; value: string }) => {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <Text className="truncate" value={value} />
    </div>
  );
};

const TrackList = ({
  title,
  tracks,
  accent,
}: {
  title: string;
  tracks: string[];
  accent: HTMLParagraphElement["className"];
}) => {
  const renderTracks = (): React.JSX.Element => {
    if (tracks.length === 0) {
      return <Text muted value="None" />;
    }

    const uniqueTracks = Array.from(new Set(tracks));

    return (
      <ScrollArea className="h-32 rounded-md border bg-secondary/50 p-2">
        <ul className="flex flex-col gap-1">
          {uniqueTracks.map((track) => (
            <li key={track} className="border-b last:border-0 py-1">
              <Text mono muted value={track} />
            </li>
          ))}
        </ul>
      </ScrollArea>
    );
  };

  return (
    <div>
      <p className={cn("mb-2 text-xs font-semibold", accent)}>{title}</p>
      {renderTracks()}
    </div>
  );
};
