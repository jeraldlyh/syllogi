import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";

interface CurrentUser {
  id: string;
  username: string;
  is_admin: boolean;
}

export const useMe = () => {
  const { data, error, isLoading } = useSWR<ApiResponse<CurrentUser>>(
    "/auth/me",
    fetcher,
  );

  return {
    data: data?.data,
    isLoading,
    isError: error,
  };
};
