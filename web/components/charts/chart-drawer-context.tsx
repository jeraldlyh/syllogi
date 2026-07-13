"use client";
import { createContext, useContext, useState } from "react";

interface AlbumSelection {
  artistName: string;
  albumName: string;
}

interface ChartDrawerContextValue {
  selectedArtist: string | null;
  setSelectedArtist: (name: string | null) => void;
  selectedAlbum: AlbumSelection | null;
  setSelectedAlbum: (album: AlbumSelection | null) => void;
}

const ChartDrawerContext = createContext<ChartDrawerContextValue | null>(null);

export const ChartDrawerProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const [selectedArtist, setSelectedArtist] = useState<string | null>(null);
  const [selectedAlbum, setSelectedAlbum] = useState<AlbumSelection | null>(
    null,
  );

  return (
    <ChartDrawerContext.Provider
      value={{
        selectedArtist,
        setSelectedArtist,
        selectedAlbum,
        setSelectedAlbum,
      }}
    >
      {children}
    </ChartDrawerContext.Provider>
  );
};

export const useChartDrawer = (): ChartDrawerContextValue => {
  const context = useContext(ChartDrawerContext);

  if (!context) {
    throw new Error("useChartDrawer must be used within a ChartDrawerProvider");
  }
  return context;
};
