"use client";
import { Music2 } from "lucide-react";
import Image from "next/image";
import { Text } from "@/components/common/text";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DownloadSession,
  useDownloadSessions,
} from "@/hooks/useDownloadSessions";
import { cn, formatDateTime } from "@/lib/utils";

const DownloadStatusBadge = ({
  status,
}: {
  status: DownloadSession["status"];
}) => {
  const labels: Record<DownloadSession["status"], string> = {
    pending: "Pending",
    downloading: "Downloading",
    completed: "Completed",
    failed: "Failed",
  };

  return (
    <Badge
      variant="outline"
      className={cn({
        "border-emerald-500/30 bg-emerald-500/10 text-emerald-400":
          status === "completed",
        "border-amber-500/30 bg-amber-500/10 text-amber-400 animate-pulse":
          status === "downloading",
        "border-red-500/30 bg-red-500/10 text-red-400": status === "failed",
        "border-muted/30 bg-muted/10 text-muted-foreground":
          status === "pending",
      })}
    >
      {labels[status]}
    </Badge>
  );
};

export const DownloadActivity = () => {
  const { data, isError, isLoading } = useDownloadSessions();

  const renderContent = (): React.JSX.Element => {
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
            value="Failed to load download activity"
          />
        </div>
      );
    }

    if (!data || data.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center gap-2 py-8">
          <Music2 className="h-8 w-8 text-muted-foreground/40" />
          <Text
            className="text-muted-foreground italic text-sm"
            value="No downloads yet"
          />
        </div>
      );
    }

    const sortedDownloads = [...data]
      .sort(
        (a, b) =>
          new Date(b.started_at).getTime() - new Date(a.started_at).getTime(),
      )
      .slice(0, 10);

    return (
      <div className="overflow-x-auto overflow-y-auto rounded-md border border-border max-h-72">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent text-xs text-muted-foreground">
              <TableHead>Track</TableHead>
              <TableHead>Artist</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="hidden sm:table-cell">Started</TableHead>
              <TableHead className="hidden sm:table-cell">Finished</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedDownloads.map((download) => (
              <TableRow key={download.id}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <Image
                      src={download.image_url}
                      alt={download.track_name}
                      width={36}
                      height={36}
                      className="rounded object-cover shrink-0 hidden md:block"
                    />
                    <Text
                      value={download.track_name}
                      className="truncate max-w-[160px]"
                    />
                  </div>
                </TableCell>
                <TableCell>
                  <Text
                    className="text-muted-foreground"
                    value={download.artist_name}
                  />
                </TableCell>
                <TableCell>
                  <DownloadStatusBadge status={download.status} />
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  <Text
                    className="text-muted-foreground text-xs"
                    value={formatDateTime(download.started_at)}
                  />
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  <Text
                    className="text-muted-foreground text-xs"
                    value={formatDateTime(download.finished_at)}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="text-base font-medium text-foreground">
          Download Activity
        </CardTitle>
      </CardHeader>
      <CardContent>{renderContent()}</CardContent>
    </Card>
  );
};
