import { ApiConfig, ApiResponse } from "./types";
import { createLogger } from "./logger";

const logger = createLogger("api");

export const api = async <T>(config: ApiConfig): Promise<ApiResponse<T>> => {
  let endpoint =
    `${process.env.NEXT_PUBLIC_URL}/api` || "http://localhost:8000/api";

  if (config.service) {
    endpoint += `/${config.service}`;
  }

  if (config.path) {
    endpoint += `/${config.path}`;
  }

  if (config.query) {
    const queryString = new URLSearchParams(config.query).toString();
    endpoint += `?${queryString}`;
  }
  logger.info(`${config.method} ${endpoint}`);

  const headers = {
    ...config.headers,
    ...(config.body && { "Content-Type": "application/json" }),
  };

  const response = await fetch(endpoint, {
    method: config.method,
    headers,
    credentials: "include",
    ...(config.cache ? { cache: config.cache } : { cache: "no-cache" }),
    ...(config.body && { body: JSON.stringify(config.body) }),
    ...(config.formData && { body: config.formData }),
  });

  const payload = await response.json();

  return {
    statusCode: response.status,
    data: payload.data as T,
    error: payload.error,
  };
};

export const fetcher = async <T>(
  path: string | URL,
  init?: RequestInit,
): Promise<T> => {
  const endpoint =
    `${process.env.NEXT_PUBLIC_URL}/api` || "http://localhost:8000/api";
  const response = await fetch(`${endpoint}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    credentials: "include",
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(
      `HTTP ${response.status} ${response.statusText}: ${payload.message}`,
    );
  }
  return response.status === 204 ? (undefined as unknown as T) : (payload as T);
};
