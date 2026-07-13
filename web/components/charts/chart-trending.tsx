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
import { ChartBadge } from "./chart-badge";
import { useChartDrawer } from "./chart-drawer-context";
import { ChartGridCard } from "./chart-grid-card";
import { ViewMode } from "./types";

export const ChartTrending = () => {
  const { setSelectedArtist, setSelectedAlbum } = useChartDrawer();
  const [search, setSearch] = useState("");
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
        track.artist_name.toLowerCase().includes(query) ||
        track.album_name.toLowerCase().includes(query)
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
            placeholder="Search by track, artist, or album..."
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
            <ChartGridCard
              key={key}
              trackName={track.track_name}
              albumName={track.album_name}
              artistName={track.artist_name}
              duration={track.duration}
              imageUrl={track.image_url}
              isExist={isExist}
              isDownloading={isDownloading}
              onArtistClick={() => setSelectedArtist(track.artist_name)}
            >
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 text-muted-foreground hover:text-foreground"
                onClick={() => handleDownload(track)}
                disabled={isDownloading || isExist}
              >
                <Download />
              </Button>
            </ChartGridCard>
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
              <TableHead>Album</TableHead>
              <TableHead className="hidden md:table-cell">Duration</TableHead>
              <TableHead className="hidden lg:table-cell">Artist</TableHead>
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
                      value={track.artist_name}
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
