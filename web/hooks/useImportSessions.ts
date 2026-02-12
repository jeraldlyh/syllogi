import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";

export interface ImportSession {
  id: string;
  provider: string;
  provider_playlist_id: string;
  provider_playlist_name: string;
  target_user_id: string;
  target_username: string;
  target_playlist_id: string;
  target_playlist_name: string;
  total_tracks: string[];
  new_tracks: string[];
  outdated_tracks: string[];
  missing_tracks: string[];
  started_at: string;
  finished_at: string;
  duration_seconds: number;
  success: boolean;
  created_at: string;
  updated_at: string;
}

export const useImportSessions = () => {
  const { data, error, isLoading } = useSWR<ApiResponse<ImportSession[]>>(
    "/import",
    fetcher,
  );

  return {
    data: data?.data,
    isLoading,
    isError: error,
  };
};
