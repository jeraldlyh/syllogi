"use client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Drawer, DrawerContent, DrawerTitle } from "@/components/ui/drawer";
import { useArtist, type ArtistInfo } from "@/hooks/useArtist";
import { Skeleton } from "@/components/ui/skeleton";
import { Dot } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import React from "react";

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

const trackVariants = {
  hidden: { opacity: 0, x: -10 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { delay: i * 0.05, duration: 0.3, ease: "easeOut" as const },
  }),
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
        <div className="flex h-64 w-64 items-center justify-center rounded-2xl bg-secondary">
          <span className="text-6xl font-bold text-muted-foreground">
            {artist.name.charAt(0).toUpperCase()}
          </span>
        </div>
      </div>
      <div className="flex flex-1 flex-col justify-center gap-4 md:items-start">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">{artist.name}</h1>
          {metadataItems.length > 0 && (
            <div className="flex mt-1 text-sm text-muted-foreground">
              {metadataItems.map((item) => (
                <>
                  <p>{item}</p>
                  <Dot className="-mx-1" />
                </>
              ))}
              {activeYears && <span>{activeYears}</span>}
            </div>
          )}
        </div>
        {artist.tags && artist.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {artist.tags.slice(0, 5).map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}
        {artist.aliases && artist.aliases.length > 0 && (
          <p className="text-sm text-muted-foreground">
            Also known as: {artist.aliases.join(", ")}
          </p>
        )}
        {artist.area && (
          <div className="flex text-sm text-muted-foreground">
            <p>Area: {artist.area}</p>
            {artist.begin_area && (
              <>
                <Dot className="-mx-1" />
                {artist.begin_area}
              </>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
};

const RecordingsSection = ({ data }: { data: ArtistInfo }) => {
  const shouldReduceMotion = useReducedMotion();

  const recordings = data.recordings ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">Recordings</CardTitle>
      </CardHeader>
      <CardContent>
        {recordings.length > 0 ? (
          <div className="max-h-96 space-y-1 overflow-y-auto">
            {recordings.map((recording, i) => (
              <motion.div
                key={`${recording.title}-${i}`}
                custom={i}
                variants={shouldReduceMotion ? undefined : trackVariants}
                initial={shouldReduceMotion ? {} : "hidden"}
                animate={shouldReduceMotion ? {} : "visible"}
                className="flex items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-secondary/50"
              >
                <span className="w-6 shrink-0 text-right font-mono text-xs text-muted-foreground">
                  {i + 1}
                </span>
                <div className="flex flex-1 flex-col overflow-hidden">
                  <span className="truncate text-sm font-medium">
                    {recording.title}
                  </span>
                  {recording.disambiguation && (
                    <span className="truncate text-xs text-muted-foreground">
                      {recording.disambiguation}
                    </span>
                  )}
                </div>
                <div className="shrink-0">
                  <span className="font-mono text-xs text-muted-foreground">
                    {recording.duration}
                  </span>
                </div>
              </motion.div>
            ))}
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
      <div className="flex-1 overflow-y-auto px-4 pb-8">
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
      <div className="flex flex-1 flex-col items-center justify-center px-4 pb-8">
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
      <div className="flex flex-1 flex-col items-center justify-center px-4 pb-8">
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
