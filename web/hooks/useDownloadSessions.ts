import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";

export interface DownloadSession {
  id: string;
  artist_name: string;
  track_name: string;
  status: "pending" | "downloading" | "completed" | "failed";
  started_at: string;
  finished_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export const useDownloadSessions = () => {
  const { data, error, isLoading, mutate } = useSWR<
    ApiResponse<DownloadSession[]>
  >("/charts/downloads", fetcher, {
    refreshInterval: (latestData) => {
      const downloads = latestData?.data ?? [];
      const hasActive = downloads.some(
        (download) =>
          download.status === "pending" || download.status === "downloading",
      );
      return hasActive ? 3000 : 30000;
    },
    revalidateOnFocus: true,
  });

  return {
    data: data?.data,
    isLoading,
    isError: error,
    mutate,
  };
};
