import { api, fetcher } from "@/lib/api";
import { ApiResponse, PROVIDERS } from "@/lib/types";
import useSWR from "swr";

export interface SyncConfig {
  id: string;
  provider: (typeof PROVIDERS)[number]["value"];
  playlist_id: string;
  playlist_name: string;
  username: string;
  enable_sync: boolean;
  enable_download: boolean;
  is_public: boolean;
  cron_expression: string;
}

export const useSyncConfigs = () => {
  const { data, error, isLoading, mutate } = useSWR<
    ApiResponse<SyncConfig[]>
  >("/sync/config", fetcher);

  return {
    data: data?.data,
    isLoading,
    isError: error,
    mutate,
  };
};

const createSyncConfig = async (
  config: Omit<SyncConfig, "id">,
): Promise<string> => {
  const response = await api<{ id: string }>({
    method: "POST",
    service: "sync",
    path: "config",
    body: config,
  });

  if (response.statusCode !== 200 || !response.data) {
    throw new Error(`Failed to create sync config: ${response.statusCode}`);
  }
  return response.data.id;
};

const updateSyncConfig = async (config: SyncConfig): Promise<string> => {
  const response = await api<{ id: string }>({
    method: "PUT",
    service: "sync",
    path: `config/${config.id}`,
    body: config,
  });

  if (response.statusCode !== 200 || !response.data) {
    throw new Error(`Failed to update sync config: ${response.statusCode}`);
  }
  return response.data.id;
};

const deleteSyncConfig = async (configId: string): Promise<void> => {
  const response = await api({
    method: "DELETE",
    service: "sync",
    path: `config/${configId}`,
  });

  if (response.statusCode !== 200 || !response.data) {
    throw new Error(`Failed to delete sync config: ${response.statusCode}`);
  }
};

export const createSyncConfigMutation = async (
  _key: string,
  { arg }: { arg: Omit<SyncConfig, "id"> },
) => {
  return await createSyncConfig(arg);
};

export const updateSyncConfigMutation = async (
  _key: string,
  { arg }: { arg: SyncConfig },
) => {
  return await updateSyncConfig(arg);
};

export const deleteSyncConfigMutation = async (
  _key: string,
  { arg }: { arg: string },
) => {
  return await deleteSyncConfig(arg);
};
