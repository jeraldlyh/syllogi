import { api, fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";
import { RecommendationStrategy } from "./useRecommendationSessions";

export interface BlendUser {
  name: string;
  lastfm_username: string;
}

export interface Recommendation {
  id: string;
  username: string;
  strategy: RecommendationStrategy;
  lastfm_username: string;
  requested_count: number;
  cron_expression: string;
  is_public: boolean;
  playlist_name: string;
  blend_users?: BlendUser[];
}

export const useRecommendations = () => {
  const { data, error, isLoading, mutate } = useSWR<
    ApiResponse<Recommendation[]>
  >("/recommendation", fetcher);

  return {
    data: data?.data,
    isLoading,
    isError: error,
    mutate,
  };
};

const createRecommendation = async (
  recommendation: Omit<Recommendation, "id">,
): Promise<string> => {
  const response = await api<{ id: string }>({
    method: "POST",
    service: "recommendation",
    body: recommendation,
  });

  if (response.statusCode !== 200 || !response.data) {
    throw new Error(`Failed to create recommendation: ${response.statusCode}`);
  }

  return response.data.id;
};

const updateRecommendation = async (
  recommendation: Recommendation,
): Promise<void> => {
  const response = await api({
    method: "PUT",
    service: "recommendation",
    path: recommendation.id,
    body: recommendation,
  });

  if (response.statusCode !== 200) {
    throw new Error(`Failed to update recommendation: ${response.statusCode}`);
  }
};

const deleteRecommendation = async (
  recommendationId: string,
): Promise<void> => {
  const response = await api({
    method: "DELETE",
    service: "recommendation",
    path: recommendationId,
  });

  if (response.statusCode !== 200) {
    throw new Error(`Failed to delete recommendation: ${response.statusCode}`);
  }
};

const generateRecommendation = async (
  recommendation: Recommendation,
): Promise<string> => {
  const response = await api<{ id: string }>({
    method: "POST",
    service: "recommendation",
    path: "generate",
    body: recommendation,
  });

  if (response.statusCode !== 200 || !response.data) {
    throw new Error(
      `Failed to generate recommendations: ${response.statusCode}`,
    );
  }

  return response.data.id;
};

export const createRecommendationMutation = async (
  _key: string,
  { arg }: { arg: Omit<Recommendation, "id"> },
) => {
  return await createRecommendation(arg);
};

export const updateRecommendationMutation = async (
  _key: string,
  { arg }: { arg: Recommendation },
) => {
  return await updateRecommendation(arg);
};

export const deleteRecommendationMutation = async (
  _key: string,
  { arg }: { arg: string },
) => {
  return await deleteRecommendation(arg);
};

export const generateRecommendationMutation = async (
  _key: string,
  { arg }: { arg: Recommendation },
) => {
  return await generateRecommendation(arg);
};
