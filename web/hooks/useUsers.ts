import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";

export interface MusicServerUser {
  id: string;
  name: string;
}

export const useMusicServerUsers = () => {
  const { data, error, isLoading } = useSWR<ApiResponse<MusicServerUser[]>>(
    "/users",
    fetcher,
  );

  return {
    data: data?.data,
    isLoading,
    isError: error,
  };
};
