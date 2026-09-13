import { Fragment } from "react";
import { Dot } from "lucide-react";
import { Text } from "@/components/common/text";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArtistAlbum } from "@/hooks/useArtist";
import { ChartImage } from "./chart-image";

interface IProps {
  album: ArtistAlbum;
  onClick: () => void;
}

export const ChartArtistAlbumCard = ({
  album,
  onClick,
}: IProps): React.JSX.Element => {
  const subtitleParts = [album.year, album.secondary_types?.[0]].filter(
    Boolean,
  );

  return (
    <Button
      type="button"
      variant="ghost"
      onClick={onClick}
      title={album.title}
      className="group h-auto w-36 shrink-0 snap-start flex-col items-stretch justify-start gap-0 rounded-none p-0 text-left hover:bg-transparent md:w-40"
    >
      <div className="relative aspect-square overflow-hidden rounded-xl border border-white/5 bg-secondary shadow-lg shadow-black/40 ring-primary/60 transition-all duration-300 group-hover:-translate-y-1 group-hover:ring-1">
        <ChartImage
          imageUrl={album.image_url}
          alt={album.title}
          className="min-h-0 min-w-0"
          textClassName="text-4xl font-bold"
        />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
        <Badge
          variant="secondary"
          className="absolute bottom-2 left-2 px-2 font-mono font-normal uppercase tracking-widest"
        >
          {album.type || "Release"}
        </Badge>
      </div>
      <Text value={album.title} variant="sm" className="truncate font-medium" />
      <div className="flex min-w-0 items-center gap-1.5">
        {subtitleParts.length > 0 ? (
          subtitleParts.map((part, index) => (
            <Fragment key={part}>
              {index > 0 && (
                <Dot className="size-3 shrink-0 fill-current text-muted-foreground" />
              )}
              <Text
                value={part}
                muted
                disableViewport
                className="min-w-0 truncate"
              />
            </Fragment>
          ))
        ) : (
          <Text value="—" muted disableViewport className="truncate" />
        )}
      </div>
    </Button>
  );
};
