import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";

export interface ArtistRecording {
  title: string;
  duration: number | null;
  disambiguation: string;
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
}

export interface ArtistInfo {
  artist: ArtistMetadata | null;
  recordings: ArtistRecording[];
}

export const useArtist = (artistName: string) => {
  const { data, error, isLoading } = useSWR<ApiResponse<ArtistInfo>>(
    `/charts/artist/${encodeURIComponent(artistName)}`,
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
