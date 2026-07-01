"use client";
import { Text } from "@/components/common/text";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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
import { TrendingTrack, useTrendingTracks } from "@/hooks/useTrendingTracks";
import { api } from "@/lib/api";
import { formatDuration } from "@/lib/utils";
import { Download, LayoutGrid, List, RefreshCw, Search } from "lucide-react";
import Image from "next/image";
import { useState } from "react";
import { toast } from "sonner";
import { ChartArtistDrawer } from "./chart-artist-drawer";
import { ChartBadge } from "./chart-badge";

type ViewMode = "list" | "grid";

export const ChartTrending = () => {
  const [search, setSearch] = useState("");
  const [selectedArtist, setSelectedArtist] = useState<string | null>(null);
  const [downloadingTracks, setDownloadingTracks] = useState<Set<string>>(
    new Set(),
  );
  const [viewMode, setViewMode] = useState<ViewMode>("grid");

  const {
    data,
    isError,
    isLoading,
    mutate: fetchTrendingTracks,
  } = useTrendingTracks();

  const { data: downloadSessions, mutate: refreshDownloads } =
    useDownloadSessions();

  const getTrackKey = (track: TrendingTrack): string =>
    track.musicbrainz_id || `${track.artist_name}||${track.track_name}`;

  const isTrackDownloading = (track: TrendingTrack): boolean => {
    if (!downloadSessions) return false;

    return downloadSessions.some(
      (session: DownloadSession) =>
        (session.status === "pending" || session.status === "downloading") &&
        session.artist_name.toLowerCase() === track.artist_name.toLowerCase() &&
        session.track_name.toLowerCase() === track.track_name.toLowerCase(),
    );
  };

  const getFilteredTracks = (): TrendingTrack[] => {
    if (isError || isLoading || !data) return [];

    return data.filter((track) => {
      const query = search.toLowerCase();
      return (
        track.track_name.toLowerCase().includes(query) ||
        track.artist_name.toLowerCase().includes(query)
      );
    });
  };

  const handleDownload = async (track: TrendingTrack): Promise<void> => {
    const key = getTrackKey(track);
    setDownloadingTracks((prev) => new Set(prev).add(key));

    const toastId = toast.loading(
      `Downloading ${track.artist_name} - ${track.track_name}...`,
    );

    try {
      const response = await api({
        method: "POST",
        service: "charts",
        path: "track",
        body: {
          artist_name: track.artist_name,
          track_name: track.track_name,
          image_url: track.image_url,
        },
      });

      if (response.statusCode !== 200) {
        const errorMessage =
          response.error?.message ||
          `${track.artist_name} - ${track.track_name}`;

        toast.error("Failed to start download", {
          description: errorMessage,
          id: toastId,
        });
        return;
      }

      toast.success("Download started", {
        description: `${track.artist_name} - ${track.track_name}`,
        id: toastId,
      });
      refreshDownloads();
    } finally {
      setDownloadingTracks((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
  };

  const renderTableHeader = (): React.JSX.Element => {
    return (
      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by track or artist..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
            disabled={isLoading || !!isError}
          />
        </div>
        <div className="flex items-center gap-1 rounded-md border border-border p-1">
          <Button
            variant={viewMode === "list" ? "secondary" : "ghost"}
            size="icon"
            className="h-7 w-7"
            onClick={() => setViewMode("list")}
          >
            <List />
          </Button>
          <Button
            variant={viewMode === "grid" ? "secondary" : "ghost"}
            size="icon"
            className="h-7 w-7"
            onClick={() => setViewMode("grid")}
          >
            <LayoutGrid />
          </Button>
        </div>
      </div>
    );
  };

  const renderGrid = (): React.JSX.Element => {
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
            value="Failed to load trending tracks"
          />
        </div>
      );
    }

    if (getFilteredTracks().length === 0) {
      return (
        <div className="flex items-center justify-center py-6">
          <Text
            className="text-muted-foreground italic"
            value={
              data && data.length === 0
                ? "No trending tracks available"
                : "No tracks match your search"
            }
          />
        </div>
      );
    }

    return (
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 max-h-[60vh] overflow-auto pr-1">
        {getFilteredTracks().map((track) => {
          const key = getTrackKey(track);
          const isDownloading =
            downloadingTracks.has(key) || isTrackDownloading(track);
          const isExist = track.exists;

          return (
            <div
              key={key}
              className="group relative flex flex-col overflow-hidden rounded-lg border border-border bg-card transition-colors hover:border-foreground/20"
            >
              <div className="relative aspect-square overflow-hidden bg-secondary">
                {track.image_url ? (
                  <Image
                    src={track.image_url}
                    alt={track.track_name}
                    fill
                    className="object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                ) : (
                  <div className="flex h-full items-center justify-center">
                    <Text
                      className="text-3xl font-bold text-muted-foreground/30"
                      value={track.track_name.charAt(0).toUpperCase()}
                    />
                  </div>
                )}
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent p-2.5">
                  <Text
                    className="text-xs text-white/90 truncate"
                    value={formatDuration(track.duration)}
                  />
                </div>
                <div className="absolute top-2 right-2">
                  <ChartBadge isExist={isExist} isDownloading={isDownloading} />
                </div>
              </div>
              <div className="flex flex-1 flex-col gap-1 p-3">
                <Text
                  className="truncate font-semibold"
                  value={track.track_name}
                />
                <Button
                  onClick={() => setSelectedArtist(track.artist_name)}
                  variant="link"
                  className="h-auto p-0 text-xs text-muted-foreground hover:text-primary justify-start"
                >
                  {track.artist_name}
                </Button>
                <div className="mt-auto flex items-center justify-between pt-2">
                  <Text
                    muted
                    className="leading-tight"
                    value={`${track.listeners.toLocaleString()} listeners`}
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-muted-foreground hover:text-foreground"
                    onClick={() => handleDownload(track)}
                    disabled={isDownloading || isExist}
                  >
                    <Download />
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
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
            value="Failed to load trending tracks"
          />
        </div>
      );
    }

    if (getFilteredTracks().length === 0) {
      return (
        <div className="flex items-center justify-center py-6">
          <Text
            className="text-muted-foreground italic"
            value={
              data && data.length === 0
                ? "No trending tracks available"
                : "No tracks match your search"
            }
          />
        </div>
      );
    }

    return (
      <div className="overflow-x-auto rounded-md border border-border max-h-[40vh]">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent text-xs text-muted-foreground">
              <TableHead>Track</TableHead>
              <TableHead>Artist</TableHead>
              <TableHead className="hidden md:table-cell">Duration</TableHead>
              <TableHead className="hidden lg:table-cell">Listeners</TableHead>
              <TableHead className="hidden lg:table-cell">Playcount</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {getFilteredTracks().map((track) => {
              const key = getTrackKey(track);
              const isDownloading =
                downloadingTracks.has(key) || isTrackDownloading(track);
              const isExist = track.exists;

              return (
                <TableRow key={key}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      {track.image_url ? (
                        <Image
                          src={track.image_url}
                          alt={track.track_name}
                          width={36}
                          height={36}
                          className="rounded object-cover shrink-0"
                        />
                      ) : (
                        <div className="h-9 w-9 rounded bg-secondary shrink-0" />
                      )}
                      <div className="flex flex-col gap-1">
                        <Text value={track.track_name} />
                        <ChartBadge
                          isExist={isExist}
                          isDownloading={isDownloading}
                        />
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Button
                      onClick={() => setSelectedArtist(track.artist_name)}
                      variant="link"
                      className="text-muted-foreground hover:text-primary transition-colors text-left px-0"
                    >
                      <Text value={track.artist_name} />
                    </Button>
                  </TableCell>
                  <TableCell className="hidden md:table-cell">
                    <Text
                      className="text-muted-foreground"
                      noWrap
                      value={formatDuration(track.duration)}
                    />
                  </TableCell>
                  <TableCell className="hidden lg:table-cell">
                    <Text
                      className="text-muted-foreground"
                      value={track.listeners.toLocaleString()}
                    />
                  </TableCell>
                  <TableCell className="hidden lg:table-cell">
                    <Text
                      className="text-muted-foreground"
                      value={track.playcount.toLocaleString()}
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-foreground"
                      onClick={() => handleDownload(track)}
                      disabled={isDownloading || isExist}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
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
            Trending Tracks
          </CardTitle>
          <Button size="sm" onClick={() => fetchTrendingTracks()}>
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </CardHeader>
        <CardContent>
          {renderTableHeader()}
          {viewMode === "list" ? renderTable() : renderGrid()}
        </CardContent>
      </Card>
      <ChartArtistDrawer
        artistName={selectedArtist}
        onClose={() => setSelectedArtist(null)}
      />
    </>
  );
};
