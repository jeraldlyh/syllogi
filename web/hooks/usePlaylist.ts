import { api, fetcher } from "@/lib/api";
import { ApiResponse, PROVIDERS } from "@/lib/types";
import useSWR from "swr";

export interface Playlist {
  id: string;
  provider: (typeof PROVIDERS)[number]["value"];
  playlist_id: string;
  playlist_name: string;
  username: string;
  enabled: boolean;
  enable_download: boolean;
  cron_expression: string;
}

export const usePlaylists = () => {
  const { data, error, isLoading, mutate } = useSWR<ApiResponse<Playlist[]>>(
    "/playlist",
    fetcher,
  );

  return {
    data: data?.data,
    isLoading,
    isError: error,
    mutate,
  };
};

const createPlaylist = async (
  playlist: Omit<Playlist, "id">,
): Promise<string> => {
  const response = await api<{ id: string }>({
    method: "POST",
    service: "playlist",
    body: playlist,
  });

  if (response.statusCode !== 200 || !response.data) {
    throw new Error(`Failed to create playlist: ${response.statusCode}`);
  }
  return response.data.id;
};

const updatePlaylist = async (playlist: Playlist): Promise<string> => {
  const response = await api<{ id: string }>({
    method: "PUT",
    service: "playlist",
    path: `/${playlist.id}`,
    body: playlist,
  });

  if (response.statusCode !== 200 || !response.data) {
    throw new Error(`Failed to update playlist: ${response.statusCode}`);
  }
  return response.data.id;
};

const deletePlaylist = async (playlistId: string): Promise<void> => {
  const response = await api({
    method: "DELETE",
    service: "playlist",
    path: `/${playlistId}`,
  });

  if (response.statusCode !== 200 || !response.data) {
    throw new Error(`Failed to delete playlist: ${response.statusCode}`);
  }
};

export const createPlaylistMutation = async (
  _key: string,
  { arg }: { arg: Omit<Playlist, "id"> },
) => {
  return await createPlaylist(arg);
};

export const updatePlaylistMutation = async (
  _key: string,
  { arg }: { arg: Playlist },
) => {
  return await updatePlaylist(arg);
};

export const deletePlaylistMutation = async (
  _key: string,
  { arg }: { arg: string },
) => {
  return await deletePlaylist(arg);
};
