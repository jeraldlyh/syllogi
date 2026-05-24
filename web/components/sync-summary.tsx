"use client";
import { useSyncSessions } from "@/hooks/useSyncSessions";
import { ListMusic, User, Music, Plus, Minus, Clock, Hash } from "lucide-react";
import { StatusBadge } from "./common/status-badge";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { capitaliseFirstLetter, formatDateTime } from "@/lib/utils";
import { Text } from "./common/text";

export const SyncSummary = () => {
  const { data, isError, isLoading } = useSyncSessions();

  if (isError || isLoading || !data || data.length === 0) return <></>;
  const latestRun = data[0];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="text-base font-medium text-foreground">
          Latest Summary
        </CardTitle>
        <StatusBadge status={latestRun.status} />
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <SummaryItem
            icon={<ListMusic className="h-4 w-4 text-primary" />}
            label="Playlist"
            value={latestRun.provider_playlist_name}
          />
          <SummaryItem
            icon={<Hash className="h-4 w-4 text-primary" />}
            label={`${capitaliseFirstLetter(latestRun.provider)} ID`}
            value={latestRun.provider_playlist_id}
            mono
          />
          <SummaryItem
            icon={<User className="h-4 w-4 text-primary" />}
            label="Jellyfin User"
            value={latestRun.target_username}
          />
          <SummaryItem
            icon={<Music className="h-4 w-4 text-primary" />}
            label="Total Tracks"
            value={latestRun.total_tracks.length}
          />
          <SummaryItem
            icon={<Plus className="h-4 w-4 text-emerald-400" />}
            label="Newly Added"
            value={latestRun.new_tracks.length}
          />
          <SummaryItem
            icon={<Minus className="h-4 w-4 text-amber-400" />}
            label="Outdated"
            value={latestRun.outdated_tracks.length}
          />
          <SummaryItem
            icon={<Clock className="h-4 w-4 text-muted-foreground" />}
            label="Duration"
            value={`${latestRun.duration_seconds}s`}
          />
          <SummaryItem
            icon={<Clock className="h-4 w-4 text-muted-foreground" />}
            label="Finished At"
            value={formatDateTime(latestRun.finished_at)}
          />
        </div>
      </CardContent>
    </Card>
  );
};

interface ISummaryItemProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  mono?: boolean;
}
const SummaryItem = ({
  icon,
  label,
  value,
  mono = false,
}: ISummaryItemProps) => {
  return (
    <div className="grid grid-cols-[auto,1fr] gap-x-2 gap-y-1">
      {icon}
      <p className="text-xs text-muted-foreground">{label}</p>
      <div />
      <Text className="truncate" value={String(value)} mono={mono} />
    </div>
  );
};
