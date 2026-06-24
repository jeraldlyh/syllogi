import { api, fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import { ApiError } from "@/lib/errors";
import useSWR from "swr";

export type MusicServerProvider = "jellyfin" | "navidrome";

export interface MusicServerUserConfig {
  id: string;
  username: string;
  lastfm_username: string;
  listenbrainz_username: string;
  provider: MusicServerProvider;
  created_at: string;
  updated_at: string;
}

interface MusicServerUserRequest {
  username: string;
  password?: string;
  lastfm_username: string;
  listenbrainz_username: string;
  provider: MusicServerProvider;
}

interface MusicServerUserUpdateRequest extends MusicServerUserRequest {
  id: string;
}

export const useMusicServerUserConfigs = () => {
  const { data, error, isLoading, mutate } = useSWR<
    ApiResponse<MusicServerUserConfig[]>
  >("/users/provider", fetcher);

  return {
    data: data?.data,
    isLoading,
    isError: error,
    mutate,
  };
};

const createMusicServerUserConfig = async (
  config: MusicServerUserRequest,
): Promise<string> => {
  const response = await api<{ id: string }>({
    method: "POST",
    service: "users",
    path: "provider",
    body: config,
  });

  if (response.statusCode !== 200 || !response.data) {
    if (response.error) {
      throw new ApiError(response.error);
    }
    throw new Error(`Failed to create user config: ${response.statusCode}`);
  }
  return response.data.id;
};

const updateMusicServerUserConfig = async (
  config: MusicServerUserUpdateRequest,
): Promise<void> => {
  const response = await api({
    method: "PUT",
    service: "users",
    path: `provider/${config.id}`,
    body: config,
  });

  if (response.statusCode !== 200) {
    if (response.error) {
      throw new ApiError(response.error);
    }
    throw new Error(`Failed to update user config: ${response.statusCode}`);
  }
};

const deleteMusicServerUserConfig = async (id: string): Promise<void> => {
  const response = await api({
    method: "DELETE",
    service: "users",
    path: `provider/${id}`,
  });

  if (response.statusCode !== 200) {
    if (response.error) {
      throw new ApiError(response.error);
    }
    throw new Error(`Failed to delete user config: ${response.statusCode}`);
  }
};

export const createMusicServerUserConfigMutation = async (
  _key: string,
  { arg }: { arg: MusicServerUserRequest },
) => {
  return await createMusicServerUserConfig(arg);
};

export const updateMusicServerUserConfigMutation = async (
  _key: string,
  { arg }: { arg: MusicServerUserUpdateRequest },
) => {
  return await updateMusicServerUserConfig(arg);
};

export const deleteMusicServerUserConfigMutation = async (
  _key: string,
  { arg }: { arg: string },
) => {
  return await deleteMusicServerUserConfig(arg);
};
