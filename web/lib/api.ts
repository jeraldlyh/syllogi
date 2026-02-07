import { IApiConfig, IApiResponse } from "./types";

export const api = async <T>(config: IApiConfig): Promise<IApiResponse<T>> => {
  let endpoint =
    `${process.env.NEXT_PUBLIC_BACKEND_URL}/api` || "http://localhost:8000/api";

  if (config.service) {
    endpoint += `/${config.service}`;
  }

  if (config.path) {
    endpoint += `${config.path}`;
  }

  if (config.query) {
    const queryString = new URLSearchParams(config.query).toString();
    endpoint += `?${queryString}`;
  }
  console.log(`[endpoint] ${config.method}: ${endpoint}`);

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
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(
      `HTTP ${response.status} ${response.statusText}: ${payload.message}`,
    );
  }

  return {
    statusCode: response.status,
    data: payload.data as T,
  };
};

export const fetcher = async <T>(
  input: string | URL,
  init?: RequestInit,
): Promise<T> => {
  const response = await fetch(input, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(
      `HTTP ${response.status} ${response.statusText}: ${payload.message}`,
    );
  }
  return response.status === 204 ? (undefined as unknown as T) : (payload as T);
};
