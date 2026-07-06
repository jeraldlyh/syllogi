import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";

export interface ArtistTrack {
  track_name: string;
  duration: number;
  exists: boolean;
  album_name: string;
  image_url: string;
}

export interface ArtistMetadata {
  id: string;
  name: string;
  type: string;
  country: string;
  gender: string;
  life_span: {
    begin: string;
    end: string | null;
  };
  area: string | null;
  begin_area: string | null;
  tags: string[];
  aliases: string[];
  image_url: string | null;
  num_of_fans: number | null;
}

export interface ArtistInfo {
  artist: ArtistMetadata | null;
  recordings: ArtistTrack[];
}

export const useArtist = (artistName: string, locale?: string) => {
  const { data, error, isLoading } = useSWR<ApiResponse<ArtistInfo>>(
    `/charts/artist/${encodeURIComponent(artistName)}${locale ? `?locale=${encodeURIComponent(locale)}` : ""}`,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    },
  );

  return {
    data: data?.data,
    isLoading,
    isError: error,
  };
};
