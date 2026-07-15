"use client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { ArtistTrack, useArtist, type ArtistInfo } from "@/hooks/useArtist";
import {
  DownloadSession,
  useDownloadSessions,
} from "@/hooks/useDownloadSessions";
import { api } from "@/lib/api";
import { capitaliseFirstLetter, cn, formatDuration } from "@/lib/utils";
import {
  Dot,
  Download,
  LayoutGrid,
  List,
  Loader2,
  RotateCcw,
} from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import React, { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ChartBadge } from "./chart-badge";
import { useChartDrawer } from "./chart-drawer-context";
import { ChartGridCard } from "./chart-grid-card";
import { Text } from "@/components/common/text";
import { ViewMode } from "./types";
import { ChartImage } from "./chart-image";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: "easeOut" as const },
  },
};

const HeroSkeleton = (): React.JSX.Element => {
  return (
    <div className="flex flex-col gap-6 md:flex-row md:items-start">
      <Skeleton className="h-64 w-64 shrink-0 rounded-2xl" />
      <div className="flex flex-1 flex-col gap-4">
        <Skeleton className="h-12 w-3/4" />
        <div className="flex gap-2">
          <Skeleton className="h-6 w-20 rounded-full" />
          <Skeleton className="h-6 w-24 rounded-full" />
          <Skeleton className="h-6 w-16 rounded-full" />
        </div>
        <div className="mt-2 flex gap-6">
          <Skeleton className="h-8 w-28" />
          <Skeleton className="h-8 w-28" />
        </div>
      </div>
    </div>
  );
};

const BodySkeleton = (): React.JSX.Element => {
  return (
    <div className="mt-10 space-y-8">
      <div>
        <Skeleton className="h-6 w-28" />
        <div className="mt-4 space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-4 w-6" />
              <Skeleton className="h-4 flex-1" />
              <Skeleton className="h-4 w-12" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const HeroSection = ({ data }: { data: ArtistInfo }): React.JSX.Element => {
  const shouldReduceMotion = useReducedMotion();
  const animationProps = shouldReduceMotion
    ? { initial: { opacity: 1 }, animate: { opacity: 1 } }
    : { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 } };

  const artist = data.artist;

  if (!artist) {
    return (
      <motion.div
        className="flex flex-col items-center gap-4 text-center my-4"
        {...animationProps}
        transition={{ duration: 0.6, ease: "easeOut" as const }}
      >
        <h1 className="text-2xl font-bold">Artist not found</h1>
        <p className="text-sm text-muted-foreground">
          We couldn&apos;t find information for this artist.
        </p>
      </motion.div>
    );
  }

  const metadataItems: string[] = [];
  if (artist.country) metadataItems.push(artist.country);
  if (artist.type) metadataItems.push(artist.type);
  if (artist.gender) metadataItems.push(capitaliseFirstLetter(artist.gender));
  if (artist.num_of_fans)
    metadataItems.push(`${artist.num_of_fans.toLocaleString()} fans`);
  // if (artist.area) metadataItems.push(artist.area);
  // if (artist.begin_area) metadataItems.push(artist.begin_area);

  if (artist.life_span?.begin)
    metadataItems.push(
      `${artist.life_span.begin} till ${artist.life_span.end ? `${artist.life_span.end}` : "present"}`,
    );

  return (
    <motion.div
      className="flex flex-col gap-6 md:flex-row md:items-start"
      {...animationProps}
      transition={{ duration: 0.6, ease: "easeOut" as const }}
    >
      <ChartImage imageUrl={artist.image_url} alt={artist.name} />
      <div className="flex flex-1 flex-col justify-center gap-2">
        <div>
          <div className="flex flex-wrap items-baseline gap-x-3">
            <h1 className="text-4xl font-bold tracking-tight">{artist.name}</h1>
            {artist.aliases && artist.aliases.length > 0 && (
              <span className="text-sm text-muted-foreground/60 truncate max-w-[300px] md:max-w-none">
                (aka {artist.aliases.join(", ")})
              </span>
            )}
          </div>
          {metadataItems.length > 0 && (
            <div className="flex mt-2 items-center text-sm text-muted-foreground">
              {metadataItems.map((item, i) => (
                <Badge key={`${item}-${i}`} variant="outline">
                  {item}
                </Badge>
              ))}
            </div>
          )}
        </div>
        {artist.tags && artist.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {artist.tags.slice(0, 10).map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
};

const TracksSection = ({ data }: { data: ArtistInfo }) => {
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
          <Loader2 className="h-4 w-4 animate-spin text-amber-400" />
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
          <RotateCcw className="h-4 w-4" />
        ) : (
          <Download className="h-4 w-4" />
        )}
      </Button>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex justify-between items-center">
          <span className="text-base font-semibold">Tracks</span>
          <div className="flex items-center gap-2">
            <div className="hidden md:flex items-center gap-1 rounded-md border border-border p-1">
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
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
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
                  <ChartGridCard
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
                  </ChartGridCard>
                );
              })}
            </div>
          ) : (
            <div className="max-h-[60vh] overflow-auto rounded-md border">
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
                        className={cn({
                          "md:bg-inherit bg-amber-500/10":
                            status === "pending" || status === "downloading",
                          "md:bg-inherit bg-emerald-500/10": track.exists,
                        })}
                      >
                        <TableCell className="hidden md:table-cell font-mono text-xs text-muted-foreground">
                          {i + 1}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-1">
                            <div className="flex flex-col gap-1">
                              <span className="truncate text-sm font-medium max-w-48 lg:max-w-none">
                                {track.track_name}
                                <Text
                                  className="md:hidden truncate max-w-48"
                                  value={track.album_name}
                                  muted
                                />
                              </span>
                            </div>
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
          <p className="text-sm italic text-muted-foreground">
            No tracks available for this artist.
          </p>
        )}
      </CardContent>
    </Card>
  );
};

const ArtistContent = ({ artistName }: { artistName: string }) => {
  const locale =
    typeof navigator !== "undefined" ? navigator.language : undefined;
  const { data, isLoading, isError } = useArtist(artistName, locale);
  const shouldReduceMotion = useReducedMotion();

  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto px-6 pb-8">
        <div className="py-6">
          <HeroSkeleton />
          <div className="mt-8">
            <BodySkeleton />
          </div>
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-6 pb-8">
        <div className="flex flex-col items-center gap-4 text-center">
          <h1 className="text-2xl font-bold mt-4">Artist not found</h1>
          <p className="text-sm text-muted-foreground">
            We couldn&apos;t find information for &quot;{artistName}&quot;.
          </p>
        </div>
      </div>
    );
  }

  if (!data.artist) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-6 pb-8">
        <div className="flex flex-col items-center gap-4 text-center">
          <h1 className="text-2xl font-bold">Artist not found</h1>
          <p className="text-sm text-muted-foreground">
            &quot;{artistName}&quot; was not found in MusicBrainz.
          </p>
        </div>
      </div>
    );
  }

  const animationProps = shouldReduceMotion
    ? { initial: { opacity: 1 }, animate: { opacity: 1 } }
    : {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        transition: { duration: 0.4 },
      };

  return (
    <motion.div
      className="flex-1 overflow-y-auto px-4 pb-8"
      {...animationProps}
    >
      <div className="py-6">
        <HeroSection data={data} />
        <motion.div
          className="mt-10"
          variants={shouldReduceMotion ? undefined : containerVariants}
          initial={shouldReduceMotion ? {} : "hidden"}
          animate={shouldReduceMotion ? {} : "visible"}
        >
          <motion.div variants={shouldReduceMotion ? undefined : itemVariants}>
            <TracksSection data={data} />
          </motion.div>
        </motion.div>
      </div>
    </motion.div>
  );
};

export const ChartArtistDrawer = ({
  artistName,
  onClose,
}: {
  artistName: string | null;
  onClose: () => void;
}) => {
  return (
    <Drawer
      open={!!artistName}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DrawerContent>
        <DrawerTitle className="sr-only">{artistName}</DrawerTitle>
        {artistName && (
          <ArtistContent key={artistName} artistName={artistName} />
        )}
      </DrawerContent>
    </Drawer>
  );
};
