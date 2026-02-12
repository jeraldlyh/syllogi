"use client";
import { SyncSession, useSyncSessions } from "@/hooks/useSyncSessions";
import { ListMusic, User, Music, Plus, Minus, Clock, Hash } from "lucide-react";
import { StatusBadge } from "./common/status-badge";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";

export const SyncSummary = () => {
  const { data, isError, isLoading } = useSyncSessions();

  if (isError || isLoading || !data || data.length === 0) return <></>;
  const latestRun = data[0];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="text-base font-medium text-foreground">
          Latest Sync Summary
        </CardTitle>
        <StatusBadge status={latestRun.success} />
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
            label="Spotify ID"
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
            label="Timestamp"
            value={latestRun.finished_at}
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
    <div className="flex items-start gap-2">
      <div className="mt-0.5 flex-shrink-0">{icon}</div>
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p
          className={`text-sm font-medium text-foreground truncate ${mono ? "font-mono text-xs" : ""}`}
        >
          {value}
        </p>
      </div>
    </div>
  );
};
