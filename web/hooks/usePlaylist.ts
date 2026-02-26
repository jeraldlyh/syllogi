import { fetcher } from "@/lib/api";
import { ApiResponse, PROVIDERS } from "@/lib/types";
import useSWR from "swr";

export interface Playlist {
  id: string;
  provider: (typeof PROVIDERS)[number]["value"];
  playlistId: string;
  playlistName: string;
  username: string;
  enabled: boolean;
  cronExpression: string;
}

export const usePlaylists = () => {
  const { data, error, isLoading } = useSWR<ApiResponse<Playlist[]>>(
    "/playlist",
    fetcher,
  );

  return {
    data: data?.data,
    isLoading,
    isError: error,
  };
};
