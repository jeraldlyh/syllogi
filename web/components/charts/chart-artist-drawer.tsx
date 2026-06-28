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
import { ArtistRecording, useArtist, type ArtistInfo } from "@/hooks/useArtist";
import {
  DownloadSession,
  useDownloadSessions,
} from "@/hooks/useDownloadSessions";
import { api } from "@/lib/api";
import { formatDuration } from "@/lib/utils";
import { Dot, Download, Loader2, RotateCcw } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import Image from "next/image";
import React from "react";
import { toast } from "sonner";
import { Button } from "../ui/button";
import { ChartBadge } from "./chart-badge";

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
        className="flex flex-col items-center gap-4 text-center"
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
  if (artist.gender) metadataItems.push(artist.gender);
  if (artist.num_of_fans)
    metadataItems.push(`${artist.num_of_fans.toLocaleString()} fans`);
  // if (artist.area) metadataItems.push(artist.area);
  // if (artist.begin_area) metadataItems.push(artist.begin_area);

  const activeYears = artist.life_span?.begin
    ? `${artist.life_span.begin} till ${artist.life_span.end ? `${artist.life_span.end}` : "present"}`
    : null;

  return (
    <motion.div
      className="flex flex-col gap-6 md:flex-row md:items-start"
      {...animationProps}
      transition={{ duration: 0.6, ease: "easeOut" as const }}
    >
      <div className="shrink-0">
        {artist.image_url ? (
          <Image
            src={artist.image_url}
            alt={artist.name}
            width={256}
            height={256}
            className="h-64 w-64 rounded-2xl object-cover"
            priority
          />
        ) : (
          <div className="flex h-64 w-64 items-center justify-center rounded-2xl bg-secondary">
            <span className="text-6xl font-bold text-muted-foreground">
              {artist.name.charAt(0).toUpperCase()}
            </span>
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col justify-center gap-4">
        <div>
          <div className="flex flex-wrap items-baseline gap-x-3">
            <h1 className="text-4xl font-bold tracking-tight">{artist.name}</h1>
            {artist.aliases && artist.aliases.length > 0 && (
              <span className="text-sm text-muted-foreground/60 truncate max-w-[200px] md:max-w-none">
                (aka {artist.aliases.join(", ")})
              </span>
            )}
          </div>
          {metadataItems.length > 0 && (
            <div className="flex mt-1 text-sm text-muted-foreground">
              {metadataItems.map((item, i) => (
                <div className="flex" key={`${item}-${i}`}>
                  <p>{item}</p>
                  <Dot className="-mx-1" />
                </div>
              ))}
              {activeYears && <span>{activeYears}</span>}
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

const RecordingsSection = ({ data }: { data: ArtistInfo }) => {
  const recordings = data.recordings ?? [];
  const artistName = data.artist ? data.artist.name : "";

  const { data: downloadSessions, mutate: refreshDownloads } =
    useDownloadSessions();

  const getRecordingStatus = (
    recording: ArtistRecording,
  ): DownloadSession["status"] | null => {
    if (!downloadSessions || !data.artist) return null;

    const session = downloadSessions.find(
      (session: DownloadSession) =>
        session.artist_name.toLowerCase() === artistName.toLowerCase() &&
        session.track_name.toLowerCase() === recording.title.toLowerCase(),
    );

    return session ? session.status : null;
  };

  const handleDownload = async (recording: ArtistRecording): Promise<void> => {
    const toastId = toast.loading(
      `Downloading ${artistName} - ${recording.title}...`,
    );

    try {
      const response = await api({
        method: "POST",
        service: "charts",
        path: "track",
        body: {
          artist_name: artistName,
          track_name: recording.title,
          image_url: "",
        },
      });

      if (response.statusCode !== 200) {
        const errorMessage =
          response.error?.message || `${artistName} - ${recording.title}`;

        toast.error("Failed to start download", {
          description: errorMessage,
          id: toastId,
        });
        return;
      }

      toast.success("Download started", {
        description: `${artistName} - ${recording.title}`,
        id: toastId,
      });
      refreshDownloads();
    } catch {
      toast.error("Failed to start download", {
        description: `${artistName} - ${recording.title}`,
        id: toastId,
      });
    }
  };

  const renderAction = (recording: ArtistRecording) => {
    const status = getRecordingStatus(recording);

    if (status === "pending" || status === "downloading") {
      return (
        <Button disabled variant="ghost">
          <Loader2 className="h-4 w-4 animate-spin text-amber-400" />
        </Button>
      );
    }

    if (recording.exists) {
      return null;
    }

    const isFailed = status === "failed";

    return (
      <Button
        type="button"
        onClick={() => handleDownload(recording)}
        variant={isFailed ? "destructive" : "ghost"}
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
        <CardTitle className="text-base font-semibold">Recordings</CardTitle>
      </CardHeader>
      <CardContent>
        {recordings.length > 0 ? (
          <div className="max-h-96 overflow-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent text-xs text-muted-foreground">
                  <TableHead className="w-10">#</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead className="w-16 text-right">Duration</TableHead>
                  <TableHead className="w-10"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recordings.map((recording, i) => {
                  const status = getRecordingStatus(recording);

                  return (
                    <TableRow key={`${recording.title}-${i}`}>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        {i + 1}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-1">
                          <span className="truncate text-sm font-medium">
                            {recording.title}
                          </span>
                          <ChartBadge
                            isExist={recording.exists}
                            isDownloading={
                              status === "pending" || status === "downloading"
                            }
                          />
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs text-muted-foreground">
                        {formatDuration(recording.duration)}
                      </TableCell>
                      <TableCell>{renderAction(recording)}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        ) : (
          <p className="text-sm italic text-muted-foreground">
            No recordings available for this artist.
          </p>
        )}
      </CardContent>
    </Card>
  );
};

const ArtistContent = ({ artistName }: { artistName: string }) => {
  const { data, isLoading, isError } = useArtist(artistName);
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
          <h1 className="text-2xl font-bold">Artist not found</h1>
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
            <RecordingsSection data={data} />
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
