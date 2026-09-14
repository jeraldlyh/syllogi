import { Text } from "@/components/common/text";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { useChartDrawer } from "./chart-drawer-context";
import { type ArtistAlbum } from "@/hooks/useArtist";
import { ChartArtistAlbumCard } from "./chart-artist-album-card";
import React, { useMemo, useRef, useState } from "react";

const ALBUM_FILTERS = ["All", "Albums", "EPs", "Singles", "Other"] as const;

type AlbumFilter = (typeof ALBUM_FILTERS)[number];

const matchesFilter = (album: ArtistAlbum, filter: AlbumFilter): boolean => {
  if (filter === "All") return true;
  if (filter === "Albums") return album.type === "Album";
  if (filter === "EPs") return album.type === "EP";
  if (filter === "Singles") return album.type === "Single";

  return !["Album", "EP", "Single"].includes(album.type);
};

export const ChartArtistDiscography = ({
  albums,
  artistName,
}: {
  albums: ArtistAlbum[];
  artistName: string;
}): React.JSX.Element => {
  const { setSelectedAlbum } = useChartDrawer();
  const [filter, setFilter] = useState<AlbumFilter>("All");
  const scrollRef = useRef<HTMLDivElement>(null);

  const counts = useMemo(() => {
    const totals: Record<AlbumFilter, number> = {
      All: albums.length,
      Albums: 0,
      EPs: 0,
      Singles: 0,
      Other: 0,
    };

    for (const album of albums) {
      if (album.type === "Album") totals.Albums += 1;
      else if (album.type === "EP") totals.EPs += 1;
      else if (album.type === "Single") totals.Singles += 1;
      else totals.Other += 1;
    }

    return totals;
  }, [albums]);

  const visibleAlbums = useMemo(
    () => albums.filter((album) => matchesFilter(album, filter)),
    [albums, filter],
  );

  const scrollByPage = (direction: 1 | -1): void => {
    const container = scrollRef.current;

    if (!container) return;

    container.scrollBy({
      left: direction * container.clientWidth * 0.8,
      behavior: "smooth",
    });
  };

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <Text
          value="Albums & Releases"
          variant="base"
          className="font-semibold"
        />
        {albums.length > 0 && (
          <div className="hidden items-center gap-1 md:flex">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={() => scrollByPage(-1)}
            >
              <ChevronLeft className="size-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={() => scrollByPage(1)}
            >
              <ChevronRight className="size-4" />
            </Button>
          </div>
        )}
      </div>
      {albums.length === 0 ? (
        <Text
          variant="sm"
          muted
          className="mt-4 italic"
          value="No releases found for this artist."
        />
      ) : (
        <>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {ALBUM_FILTERS.map((option) =>
              counts[option] > 0 ? (
                <button
                  key={option}
                  type="button"
                  onClick={() => setFilter(option)}
                  className={cn(
                    "rounded-full border px-3 py-1 text-xs transition-colors",
                    filter === option
                      ? "border-primary/40 bg-primary/15 text-primary"
                      : "border-border text-muted-foreground hover:border-foreground/20 hover:text-foreground",
                  )}
                >
                  {option}
                  <span className="ml-1.5 opacity-50">{counts[option]}</span>
                </button>
              ) : null,
            )}
          </div>
          <div className="relative mt-4">
            <div
              ref={scrollRef}
              className="-mx-4 flex snap-x snap-mandatory gap-3 overflow-x-auto px-4 pb-2 scroll-pl-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden md:-mx-6 md:px-6 md:scroll-pl-6"
            >
              {visibleAlbums.map((album) => (
                <ChartArtistAlbumCard
                  key={album.id}
                  album={album}
                  onClick={() =>
                    setSelectedAlbum({
                      artistName,
                      albumName: album.title,
                    })
                  }
                />
              ))}
            </div>
            <div className="pointer-events-none absolute inset-y-0 -right-4 w-10 bg-gradient-to-l from-background to-transparent md:-right-6" />
          </div>
          {visibleAlbums.length === 0 && (
            <Text
              variant="sm"
              muted
              className="mt-3 italic"
              value="No releases match this filter."
            />
          )}
        </>
      )}
    </>
  );
};
