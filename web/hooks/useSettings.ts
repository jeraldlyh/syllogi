import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";
import { MusicServerProvider } from "./useMusicServerUsers";

export interface Settings {
  is_oauth_enabled: boolean;
  music_providers: MusicServerProvider[];
}

export const useSettings = () => {
  const { data, error, isLoading } = useSWR<ApiResponse<Settings>>(
    "/settings",
    fetcher,
  );

  return {
    data: {
      isOAuthEnabled: data && data.data ? data.data.is_oauth_enabled : false,
      musicProviders: data && data.data ? data.data.music_providers : [],
    },
    isLoading,
    isError: error,
  };
};
