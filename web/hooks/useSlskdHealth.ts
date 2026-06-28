import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";

interface SlskdHealth {
  configured: boolean;
  connected: boolean;
}

export const useSlskdHealth = () => {
  const { data, error, isLoading } = useSWR<ApiResponse<SlskdHealth>>(
    "/health/slskd",
    fetcher,
    {
      refreshInterval: 5000,
      revalidateOnFocus: true,
      revalidateOnReconnect: true,
    },
  );

  return {
    data: data?.data,
    isLoading,
    isError: error,
  };
};
