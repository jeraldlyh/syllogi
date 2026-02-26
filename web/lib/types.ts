export interface ApiConfig {
  method: "GET" | "POST" | "PUT" | "DELETE";
  body?: any;
  headers?: Record<string, string>;
  service: "" | "spotify" | "log";
  path?: string;
  query?: Record<string, any>;
  cache?: RequestCache;
}

export interface ApiResponse<T> {
  statusCode: number;
  errorMessage?: string;
  data?: T;
}

export const PROVIDERS = [
  { label: "Spotify", value: "spotify" },
  { label: "Youtube", value: "youtube" },
] as const;

export const CRON_PRESETS = [
  { label: "Every 15 minutes", value: "*/15 * * * *" },
  { label: "Every 30 minutes", value: "*/30 * * * *" },
  { label: "Every hour", value: "0 * * * *" },
  { label: "Every 6 hours", value: "0 */6 * * *" },
  { label: "Every 12 hours", value: "0 */12 * * *" },
  { label: "Daily at midnight", value: "0 0 * * *" },
  { label: "Daily at 6 AM", value: "0 6 * * *" },
  { label: "Weekly (Sunday midnight)", value: "0 0 * * 0" },
];
