import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";

export interface Settings {
  is_oauth_enabled: boolean;
}

export const useSettings = () => {
  const { data, error, isLoading } = useSWR<ApiResponse<Settings>>(
    "/settings",
    fetcher,
  );

  return {
    data: {
      isOAuthEnabled: data && data.data ? data.data.is_oauth_enabled : false,
    },
    isLoading,
    isError: error,
  };
};
