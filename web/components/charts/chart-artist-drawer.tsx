import { Button } from "@/components/ui/button";
import { Drawer, DrawerContent, DrawerTitle } from "@/components/ui/drawer";
import { useArtist } from "@/hooks/useArtist";
import { X } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { ChartArtistDiscography } from "./chart-artist-discography";
import { ChartArtistEmptyState } from "./chart-artist-empty-state";
import { ChartArtistHero } from "./chart-artist-hero";
import { ChartArtistSkeleton } from "./chart-artist-skeleton";
import { ChartArtistTracks } from "./chart-artist-tracks";

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: "easeOut" as const },
  },
};

const ArtistContent = ({ artistName }: { artistName: string }) => {
  const locale =
    typeof navigator !== "undefined" ? navigator.language : undefined;
  const { data, isLoading, isError } = useArtist(artistName, locale);
  const shouldReduceMotion = useReducedMotion();

  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto pb-8">
        <ChartArtistSkeleton />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <ChartArtistEmptyState
        title="Artist not found"
        description={`We couldn't find information for "${artistName}".`}
      />
    );
  }

  if (!data.artist) {
    return (
      <ChartArtistEmptyState
        title="Artist not found"
        description={`"${artistName}" was not found in MusicBrainz.`}
      />
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
      className="relative flex-1 overflow-y-auto pb-8"
      {...animationProps}
    >
      <div className="relative flex flex-col gap-8 px-4 py-6 md:px-6">
        <ChartArtistHero data={data} />
        <motion.div variants={shouldReduceMotion ? undefined : itemVariants}>
          <ChartArtistDiscography
            albums={data.albums}
            artistName={data.artist.name}
          />
        </motion.div>
        <motion.div variants={shouldReduceMotion ? undefined : itemVariants}>
          <ChartArtistTracks data={data} />
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
      <DrawerContent className="rounded-t-2xl border-white/10">
        <DrawerTitle className="sr-only">{artistName}</DrawerTitle>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onClose}
          className="absolute right-3 top-3 z-30 h-8 w-8 rounded-full border border-white/10 bg-black/40 text-muted-foreground backdrop-blur transition-colors hover:bg-black/60 hover:text-foreground"
        >
          <X className="size-4" />
        </Button>
        {artistName && (
          <ArtistContent key={artistName} artistName={artistName} />
        )}
      </DrawerContent>
    </Drawer>
  );
};
