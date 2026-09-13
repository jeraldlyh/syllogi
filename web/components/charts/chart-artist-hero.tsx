import { Text } from "@/components/common/text";
import { Badge } from "@/components/ui/badge";
import { capitaliseFirstLetter } from "@/lib/utils";
import { type ArtistInfo } from "@/hooks/useArtist";
import { Calendar, MapPin, Music2, Users } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import React from "react";
import { ChartImage } from "./chart-image";

export const ChartArtistHero = ({
  data,
}: {
  data: ArtistInfo;
}): React.JSX.Element => {
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
        <Text
          variant="sm"
          muted
          value="We couldn't find information for this artist."
        />
      </motion.div>
    );
  }

  const metaItems: { icon: React.ReactNode; label: string }[] = [];
  const typeAndGender = [
    artist.type,
    artist.gender ? capitaliseFirstLetter(artist.gender) : "",
  ]
    .filter(Boolean)
    .join(" · ");

  if (typeAndGender) {
    metaItems.push({
      icon: <Music2 className="size-3.5 text-primary/70" />,
      label: typeAndGender,
    });
  }

  const location = artist.area || artist.country;

  if (location) {
    metaItems.push({
      icon: <MapPin className="size-3.5 text-primary/70" />,
      label: location,
    });
  }

  if (artist.life_span?.begin) {
    metaItems.push({
      icon: <Calendar className="size-3.5 text-primary/70" />,
      label: `${artist.life_span.begin} – ${artist.life_span.end ?? "present"}`,
    });
  }

  if (artist.num_of_fans) {
    metaItems.push({
      icon: <Users className="size-3.5 text-primary/70" />,
      label: `${artist.num_of_fans.toLocaleString()} fans`,
    });
  }

  return (
    <motion.div
      className="flex flex-col gap-6 md:flex-row"
      {...animationProps}
      transition={{ duration: 0.6, ease: "easeOut" as const }}
    >
      <ChartImage imageUrl={artist.image_url} alt={artist.name} />
      <div className="flex flex-1 flex-col justify-center">
        <div className="flex flex-wrap items-baseline gap-x-3">
          <h1 className="text-4xl font-bold tracking-tight">{artist.name}</h1>
          {artist.aliases && artist.aliases.length > 0 && (
            <span className="text-sm text-muted-foreground/60 truncate max-w-[300px] md:max-w-none">
              (aka {artist.aliases.join(", ")})
            </span>
          )}
        </div>
        {artist.tags && artist.tags.length > 0 && (
          <div className="flex mt-2 flex-wrap gap-2">
            {artist.tags.slice(0, 10).map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}
        {metaItems.length > 0 && (
          <div className="flex md:mt-auto mt-2 flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-muted-foreground">
            {metaItems.map((item, i) => (
              <React.Fragment key={item.label}>
                {i > 0 && <span aria-hidden className="h-3 w-px bg-border" />}
                <span className="text-sm inline-flex items-center gap-1.5">
                  {item.icon}
                  {item.label}
                </span>
              </React.Fragment>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
};
