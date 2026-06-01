import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";

export interface TrendingTrack {
  artist_name: string;
  track_name: string;
  duration: number;
  listeners: number;
  playcount: number;
  musicbrainz_id: string;
  image_url: string;
  exists: boolean;
}

export const useTrendingTracks = () => {
  const { data, error, isLoading, mutate } = useSWR<
    ApiResponse<TrendingTrack[]>
  >("/charts/trending", fetcher, {
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
  });

  return {
    data: data?.data,
    isLoading,
    isError: error,
    mutate,
  };
};
