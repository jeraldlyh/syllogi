import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";

export interface LogRecord {
  timestamp: string;
  level: string;
  module: string;
  message: string;
}

export const useLogs = () => {
  const { data, error, isLoading } = useSWR<ApiResponse<LogRecord[]>>(
    "/logs",
    fetcher,
    { refreshInterval: 5000 },
  );

  return {
    data: data?.data,
    isLoading,
    isError: error,
  };
};
