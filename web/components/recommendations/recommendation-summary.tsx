"use client";
import { useRecommendationSessions } from "@/hooks/useRecommendationSessions";
import { User, Music, Plus, Minus, Clock, Hash } from "lucide-react";
import { StatusBadge } from "@/components/common/status-badge";
import { RecommendationProviderBadge } from "./recommendation-provider-badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { formatDateTime, formatDuration } from "@/lib/utils";
import { SummaryItem } from "@/components/common/summary-item";
import { RecommendationStrategyBadge } from "./recommendation-strategy-badge";

export const RecommendationSummary = () => {
  const { data, isError, isLoading } = useRecommendationSessions();

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
            icon={<Hash className="h-4 w-4 text-primary" />}
            label="Provider"
            value={
              <RecommendationProviderBadge provider={latestRun.provider} />
            }
          />
          <SummaryItem
            icon={<Music className="h-4 w-4 text-primary" />}
            label="Strategy"
            value={
              <RecommendationStrategyBadge strategy={latestRun.strategy} />
            }
          />
          <SummaryItem
            icon={<User className="h-4 w-4 text-primary" />}
            label="User"
            value={latestRun.username}
          />
          <SummaryItem
            icon={<Music className="h-4 w-4 text-primary" />}
            label="Requested"
            value={latestRun.requested_count}
          />
          <SummaryItem
            icon={<Plus className="h-4 w-4 text-emerald-400" />}
            label="Matched"
            value={latestRun.matched_tracks.length}
          />
          <SummaryItem
            icon={<Minus className="h-4 w-4 text-amber-400" />}
            label="Missing"
            value={latestRun.missing_tracks.length}
          />
          <SummaryItem
            icon={<Clock className="h-4 w-4 text-muted-foreground" />}
            label="Duration"
            value={formatDuration(latestRun.duration_seconds)}
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
