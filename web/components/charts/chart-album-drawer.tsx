"use client";
import { Text } from "@/components/common/text";
import { Button } from "@/components/ui/button";
import { Drawer, DrawerContent, DrawerTitle } from "@/components/ui/drawer";
import { Skeleton } from "@/components/ui/skeleton";
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
import { useAlbum } from "@/hooks/useAlbum";
import { api } from "@/lib/api";
import { cn, formatDuration } from "@/lib/utils";
import { Dot, Download, Loader2, RotateCcw } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { ChartBadge } from "./chart-badge";
import { ArtistTrack } from "@/hooks/useArtist";
import { ChartImage } from "./chart-image";
import { Badge } from "../ui/badge";

interface IProps {
  artistName: string;
  albumName: string;
}

const AlbumContent = ({ artistName, albumName }: IProps) => {
  const { data, isLoading, isError } = useAlbum(artistName, albumName);
  const [downloadingTracks, setDownloadingTracks] = useState<Set<string>>(
    new Set(),
  );
  const { data: downloadSessions, mutate: refreshDownloads } =
    useDownloadSessions();

  const getTrackKey = (track: ArtistTrack): string =>
    `${artistName.toLowerCase()}:${track.track_name.toLowerCase()}`;

  const getTrackStatus = (
    track: ArtistTrack,
  ): DownloadSession["status"] | null => {
    if (!downloadSessions) return null;

    const session = downloadSessions.find(
      (s: DownloadSession) =>
        s.artist_name.toLowerCase() === artistName.toLowerCase() &&
        s.track_name.toLowerCase() === track.track_name.toLowerCase(),
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
        toast.error("Failed to start download", {
          description:
            response.error?.message || `${artistName} - ${track.track_name}`,
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
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
  };

  const renderAction = (track: ArtistTrack) => {
    const status = getTrackStatus(track);
    const isStarting = downloadingTracks.has(getTrackKey(track));

    if (isStarting || status === "pending" || status === "downloading") {
      return (
        <Button disabled variant="ghost" size="icon" className="h-7 w-7">
          <Loader2 className="h-4 w-4 animate-spin text-amber-400" />
        </Button>
      );
    }

    if (track.exists) return null;

    const isFailed = status === "failed";
    return (
      <Button
        type="button"
        onClick={() => handleDownload(track)}
        variant="ghost"
        size="icon"
        className="h-7 w-7 text-muted-foreground hover:text-foreground"
      >
        {isFailed ? (
          <RotateCcw className="h-4 w-4" />
        ) : (
          <Download className="h-4 w-4" />
        )}
      </Button>
    );
  };

  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto px-6 pb-8">
        <div className="py-6 flex flex-col gap-6 md:flex-row md:items-start">
          <Skeleton className="h-48 w-48 shrink-0 rounded-xl" />
          <div className="flex flex-1 flex-col gap-3">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-5 w-1/2" />
          </div>
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-6 pb-8">
        <div className="flex flex-col items-center gap-4 text-center">
          <h1 className="text-2xl font-bold mt-4">Album not found</h1>
          <p className="text-sm text-muted-foreground">
            We couldn&apos;t find information for &quot;{albumName}&quot;.
          </p>
        </div>
      </div>
    );
  }

  const tracks = data.tracks;

  return (
    <div className="flex-1 overflow-y-auto px-4 pb-8">
      <div className="py-6">
        <div className="flex flex-col gap-6 md:flex-row md:items-start">
          <ChartImage imageUrl={data.image_url} alt={data.title} />
          <div className="flex flex-1 flex-col justify-center gap-2">
            <h1 className="text-3xl font-bold tracking-tight">{data.title}</h1>
            <Text className="font-semibold" value={data.artist_name} />
            <div className="flex gap-2">
              {data.release_date && (
                <Badge variant="secondary">{data.release_date}</Badge>
              )}
              {tracks.length > 0 && (
                <Badge variant="secondary">{tracks.length} tracks</Badge>
              )}
            </div>
          </div>
        </div>
        <div className="mt-8">
          {tracks.length > 0 ? (
            <div className="overflow-auto rounded-md border max-h-[50vh]">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent text-xs text-muted-foreground">
                    <TableHead className="w-10">#</TableHead>
                    <TableHead>Track</TableHead>
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
                        className={cn({
                          "md:bg-inherit bg-amber-500/10":
                            status === "pending" || status === "downloading",
                          "md:bg-inherit bg-emerald-500/10": track.exists,
                        })}
                      >
                        <TableCell className="font-mono text-xs text-muted-foreground">
                          {i + 1}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-1">
                            <span className="truncate text-sm font-medium">
                              {track.track_name}
                            </span>
                            <ChartBadge
                              isExist={track.exists}
                              isDownloading={
                                status === "pending" || status === "downloading"
                              }
                            />
                          </div>
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
          ) : (
            <p className="text-sm italic text-muted-foreground">
              No tracks available for this album.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export const ChartAlbumDrawer = ({
  artistName,
  albumName,
  onClose,
}: {
  artistName: string | null;
  albumName: string | null;
  onClose: () => void;
}) => {
  return (
    <Drawer
      open={!!artistName && !!albumName}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DrawerContent>
        <DrawerTitle className="sr-only">{albumName}</DrawerTitle>
        {artistName && albumName && (
          <AlbumContent
            key={`${artistName}:${albumName}`}
            artistName={artistName}
            albumName={albumName}
          />
        )}
      </DrawerContent>
    </Drawer>
  );
};
