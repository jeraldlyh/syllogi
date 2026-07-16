"use client";
import { ChartAlbumDrawer } from "./chart-album-drawer";
import { ChartArtistDrawer } from "./chart-artist-drawer";
import { ChartDrawerProvider, useChartDrawer } from "./chart-drawer-context";
import { ChartTrending } from "./chart-trending";

const ChartsContent = () => {
  const { selectedArtist, setSelectedArtist, selectedAlbum, setSelectedAlbum } =
    useChartDrawer();

  return (
    <div>
      <ChartTrending />
      <ChartArtistDrawer
        artistName={selectedArtist}
        onClose={() => setSelectedArtist(null)}
      />
      <ChartAlbumDrawer
        artistName={selectedAlbum?.artistName ?? null}
        albumName={selectedAlbum?.albumName ?? null}
        onClose={() => setSelectedAlbum(null)}
      />
    </div>
  );
};

export const Charts = () => {
  return (
    <ChartDrawerProvider>
      <ChartsContent />
    </ChartDrawerProvider>
  );
};
