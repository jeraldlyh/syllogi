import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";

export type RecommendationStrategy =
  | "top_tracks"
  | "recent_tracks"
  | "mixed"
  | "blend";
export type RecommendationProvider = "lastfm";

export interface RecommendationSession {
  id: string;
  username: string;
  provider: RecommendationProvider;
  strategy: RecommendationStrategy;
  requested_count: number;
  generated_count: number;
  total_tracks: string[];
  matched_tracks: string[];
  missing_tracks: string[];
  downloaded_tracks: string[];
  started_at: string;
  finished_at: string;
  duration_seconds: number;
  status: "pending" | "completed" | "failed";
  error_message: string | null;
  blend_users?: string[] | null;
}

export const useRecommendationSessions = () => {
  const { data, error, isLoading, mutate } = useSWR<
    ApiResponse<RecommendationSession[]>
  >("/recommendation_session", fetcher);

  return {
    data: data?.data,
    isLoading,
    isError: error,
    mutate,
  };
};
