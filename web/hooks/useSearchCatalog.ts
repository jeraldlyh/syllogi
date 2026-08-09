import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";

export const MIN_SEARCH_QUERY_LENGTH = 2;

export interface SearchArtist {
  id: string;
  name: string;
  image_url: string | null;
}

export interface SearchTrack {
  artist_name: string;
  track_name: string;
  album_name: string;
  duration: number;
  image_url: string;
  exists: boolean;
}

export interface SearchResults {
  artists: SearchArtist[];
  tracks: SearchTrack[];
}

export const useSearchCatalog = (query: string) => {
  const trimmed = query.trim();
  const shouldFetch = trimmed.length >= MIN_SEARCH_QUERY_LENGTH;

  const { data, error, isLoading } = useSWR<ApiResponse<SearchResults>>(
    shouldFetch ? `/charts/search?q=${encodeURIComponent(trimmed)}` : null,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      keepPreviousData: true,
    },
  );

  return {
    data: data?.data,
    isLoading: shouldFetch && isLoading,
    isError: error,
  };
};
