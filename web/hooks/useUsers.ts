import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";

export interface JellyfinUser {
  id: string;
  name: string;
}

export const useJellyfinUsers = () => {
  const { data, error, isLoading } = useSWR<ApiResponse<JellyfinUser[]>>(
    "/jellyfin/users",
    fetcher,
  );

  return {
    data: data?.data,
    isLoading,
    isError: error,
  };
};
