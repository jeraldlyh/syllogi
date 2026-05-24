"use client";

import { useState } from "react";
import { RefreshCw, Search } from "lucide-react";

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
import { capitaliseFirstLetter, cn, formatDateTime } from "@/lib/utils";
import {
  RecommendationSession,
  useRecommendationSessions,
} from "@/hooks/useRecommendationSessions";

export const RecommendationTable = () => {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedSession, setSelectedSession] =
    useState<RecommendationSession | null>(null);

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
            <ScrollArea className="max-h-64 mt-2 rounded-md border bg-secondary/50 p-2">
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
            value={`${selectedSession.duration_seconds}s`}
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
          <Text className="text-muted-foreground italic" value="Loading..." />
        </div>
      );
    }

    if (isError) {
      return (
        <div className="flex items-center justify-center py-6">
          <Text
            className="text-muted-foreground italic text-red-400"
            value="Failed to load recommendation sessions"
          />
        </div>
      );
    }

    if (getFilteredSessions().length === 0) {
      return (
        <div className="flex items-center justify-center py-6">
          <Text
            className="text-muted-foreground italic"
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
              <TableHead>Time</TableHead>
              <TableHead>User</TableHead>
              <TableHead className="hidden sm:table-cell">Strategy</TableHead>
              <TableHead className="hidden md:table-cell">Requested</TableHead>
              <TableHead className="hidden md:table-cell">Matched</TableHead>
              <TableHead className="hidden lg:table-cell">Missing</TableHead>
              <TableHead className="hidden lg:table-cell">Duration</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {getFilteredSessions().map((session) => (
              <TableRow
                key={session.id}
                className="cursor-pointer transition-colors hover:bg-secondary/50"
                onClick={() => setSelectedSession(session)}
              >
                <TableCell>
                  <Text
                    className="text-muted-foreground"
                    value={formatDateTime(session.finished_at)}
                  />
                </TableCell>
                <TableCell>
                  <Text value={session.username} />
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  <Text
                    className="text-muted-foreground"
                    value={capitaliseFirstLetter(
                      session.strategy.replace("_", " "),
                    )}
                  />
                </TableCell>
                <TableCell className="hidden md:table-cell">
                  <Text
                    className="text-muted-foreground"
                    value={String(session.requested_count)}
                  />
                </TableCell>
                <TableCell className="hidden md:table-cell text-emerald-400">
                  <Text value={String(session.matched_tracks.length)} />
                </TableCell>
                <TableCell className="hidden lg:table-cell text-amber-400">
                  <Text value={String(session.missing_tracks.length)} />
                </TableCell>
                <TableCell className="hidden lg:table-cell">
                  <Text
                    className="text-muted-foreground"
                    value={`${session.duration_seconds}s`}
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
      return <p className="text-xs text-muted-foreground">None</p>;
    }

    const uniqueTracks = Array.from(new Set(tracks));

    return (
      <ScrollArea className="h-32 rounded-md border bg-secondary/50 p-2">
        <ul className="flex flex-col gap-1">
          {uniqueTracks.map((track) => (
            <li key={track} className="border-b last:border-0 py-1">
              <Text
                value={track}
                mono
                className="text-xs text-muted-foreground leading-relaxed"
              />
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
