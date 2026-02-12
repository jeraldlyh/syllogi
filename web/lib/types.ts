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
