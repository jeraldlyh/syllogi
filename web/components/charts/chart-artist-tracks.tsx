import { Text } from "@/components/common/text";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ArtistTrack, type ArtistInfo } from "@/hooks/useArtist";
import {
  DownloadSession,
  useDownloadSessions,
} from "@/hooks/useDownloadSessions";
import { api } from "@/lib/api";
import { cn, formatDuration } from "@/lib/utils";
import {
  Dot,
  Download,
  LayoutGrid,
  List,
  Loader2,
  RotateCcw,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { ChartBadge } from "./chart-badge";
import { useChartDrawer } from "./chart-drawer-context";
import { ChartImage } from "./chart-image";
import { ChartSearchTrackCard } from "./chart-search-track-card";
import { ViewMode } from "./types";

export const ChartArtistTracks = ({ data }: { data: ArtistInfo }) => {
  const tracks = data.tracks;
  const artistName = data.artist ? data.artist.name : "";
  const [downloadingTracks, setDownloadingTracks] = useState<Set<string>>(
    new Set(),
  );

  const { data: downloadSessions, mutate: refreshDownloads } =
    useDownloadSessions();

  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const { setSelectedAlbum } = useChartDrawer();

  const getTrackKey = (track: ArtistTrack): string =>
    `${artistName.toLowerCase()}:${track.track_name.toLowerCase()}`;

  const getTrackStatus = (
    track: ArtistTrack,
  ): DownloadSession["status"] | null => {
    if (!downloadSessions || !data.artist) return null;

    const session = downloadSessions.find(
      (session: DownloadSession) =>
        session.artist_name.toLowerCase() === artistName.toLowerCase() &&
        session.track_name.toLowerCase() === track.track_name.toLowerCase(),
    );

    return session ? session.status : null;
  };

  const handleDownload = async (track: ArtistTrack): Promise<void> => {
    const key = getTrackKey(track);

    if (downloadingTracks.has(key)) return;

    setDownloadingTracks((prev) => new Set(prev).add(key));

    const toastId = toast.loading(
      `Downloading ${artistName} - ${track.track_name}...`,
    );

    try {
      const response = await api({
        method: "POST",
        service: "charts",
        path: "track",
        body: {
          artist_name: artistName,
          track_name: track.track_name,
          image_url: "",
        },
      });

      if (response.statusCode !== 200) {
        const errorMessage =
          response.error?.message || `${artistName} - ${track.track_name}`;

        toast.error("Failed to start download", {
          description: errorMessage,
          id: toastId,
        });
        return;
      }

      toast.success("Download started", {
        description: `${artistName} - ${track.track_name}`,
        id: toastId,
      });
      refreshDownloads();
    } catch {
      toast.error("Failed to start download", {
        description: `${artistName} - ${track.track_name}`,
        id: toastId,
      });
    } finally {
      setDownloadingTracks((prev) => {
        const remaining = new Set(prev);
        remaining.delete(key);

        return remaining;
      });
    }
  };

  const renderAction = (track: ArtistTrack) => {
    const status = getTrackStatus(track);
    const isStarting = downloadingTracks.has(getTrackKey(track));

    if (isStarting || status === "pending" || status === "downloading") {
      return (
        <Button disabled variant="ghost">
          <Loader2 className="size-4 animate-spin text-amber-400" />
        </Button>
      );
    }

    const isFailed = status === "failed";

    return (
      <Button
        type="button"
        className="w-full"
        onClick={() => handleDownload(track)}
        variant={isFailed ? "destructive" : "outline"}
        disabled={track.exists}
        size="sm"
      >
        {isFailed ? (
          <RotateCcw className="size-4" />
        ) : (
          <Download className="size-4" />
        )}
      </Button>
    );
  };

  const inLibrary = tracks.filter((track) => track.exists).length;

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Top Tracks</h2>
          {tracks.length > 0 && (
            <div className="mt-1 flex text-muted-foreground">
              <Text value={`${tracks.length} tracks`} disableViewport />
              <Dot className="size-3 shrink-0 fill-current" />
              <Text value={`${inLibrary} in library`} disableViewport />
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {tracks.length > 0 && (
            <div className="hidden md:flex items-center gap-1 rounded-md border border-border p-1">
              <Button
                variant={viewMode === "list" ? "secondary" : "ghost"}
                size="icon"
                className="h-7 w-7"
                onClick={() => setViewMode("list")}
                aria-label="List view"
              >
                <List />
              </Button>
              <Button
                variant={viewMode === "grid" ? "secondary" : "ghost"}
                size="icon"
                className="size-7"
                onClick={() => setViewMode("grid")}
                aria-label="Grid view"
              >
                <LayoutGrid />
              </Button>
            </div>
          )}
          {tracks.length > 0 && (
            <div className="flex items-center gap-2 md:hidden">
              <div className="flex items-center gap-1">
                <span className="inline-block h-2 w-2 rounded-full bg-emerald-500/60" />
                <Text value="In Library" muted />
              </div>
              <div className="flex items-center gap-1">
                <span className="inline-block h-2 w-2 rounded-full bg-amber-500/60" />
                <Text value="Downloading" muted />
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="mt-4">
        {tracks.length > 0 ? (
          viewMode === "grid" ? (
            <div className="grid grid-cols-2 gap-3 md:grid-cols-5 max-h-[60vh] overflow-auto">
              {tracks.map((track, i) => {
                const status = getTrackStatus(track);
                const isStarting = downloadingTracks.has(getTrackKey(track));
                const isDownloading =
                  isStarting ||
                  status === "pending" ||
                  status === "downloading";

                return (
                  <ChartSearchTrackCard
                    key={`${track.track_name}-${i}`}
                    trackName={track.track_name}
                    albumName={track.album_name}
                    duration={track.duration}
                    imageUrl={track.image_url}
                    isExist={track.exists}
                    isDownloading={isDownloading}
                    onAlbumClick={
                      track.album_name
                        ? () =>
                            setSelectedAlbum({
                              artistName,
                              albumName: track.album_name,
                            })
                        : undefined
                    }
                  >
                    {renderAction(track)}
                  </ChartSearchTrackCard>
                );
              })}
            </div>
          ) : (
            <div className="max-h-[60vh] overflow-auto rounded-xl border border-white/5">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent text-xs text-muted-foreground">
                    <TableHead className="hidden md:table-cell w-10">
                      #
                    </TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead className="hidden md:table-cell">
                      Album
                    </TableHead>
                    <TableHead className="hidden md:table-cell w-16 text-right">
                      Duration
                    </TableHead>
                    <TableHead className="w-10"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tracks.map((track, i) => {
                    const status = getTrackStatus(track);

                    return (
                      <TableRow
                        key={`${track.track_name}-${i}`}
                        className={cn("group transition-colors", {
                          "md:bg-inherit bg-amber-500/10":
                            status === "pending" || status === "downloading",
                          "md:bg-inherit bg-emerald-500/10": track.exists,
                        })}
                      >
                        <TableCell className="hidden md:table-cell font-mono text-xs text-muted-foreground">
                          {i + 1}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <ChartImage
                              imageUrl={track.image_url}
                              alt={track.track_name}
                              className="h-10 w-10 min-h-10 min-w-10 rounded-md"
                              textClassName="text-sm"
                            />
                            <div className="flex min-w-0 flex-col gap-1">
                              <span className="truncate text-sm font-medium max-w-48 lg:max-w-none">
                                {track.track_name}
                              </span>
                              <Text
                                className="md:hidden truncate max-w-48"
                                value={track.album_name}
                                muted
                              />
                              <div className="hidden md:block">
                                <ChartBadge
                                  isExist={track.exists}
                                  isDownloading={
                                    status === "pending" ||
                                    status === "downloading"
                                  }
                                />
                              </div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="hidden md:table-cell">
                          <Button
                            onClick={() =>
                              setSelectedAlbum({
                                artistName,
                                albumName: track.album_name,
                              })
                            }
                            variant="link"
                            className="text-muted-foreground hover:text-primary transition-colors text-left px-0"
                            disabled={!track.album_name}
                          >
                            <Text value={track.album_name} />
                          </Button>
                        </TableCell>
                        <TableCell className="hidden md:table-cell">
                          <Text
                            value={formatDuration(track.duration)}
                            muted
                            noWrap
                          />
                        </TableCell>
                        <TableCell>{renderAction(track)}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )
        ) : (
          <Text
            variant="sm"
            muted
            className="italic"
            value="No tracks available for this artist."
          />
        )}
      </div>
    </section>
  );
};
