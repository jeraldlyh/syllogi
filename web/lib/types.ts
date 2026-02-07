export interface IApiConfig {
  method: "GET" | "POST" | "PUT" | "DELETE";
  body?: any;
  headers?: Record<string, string>;
  service: "" | "spotify" | "log";
  path?: string;
  query?: Record<string, any>;
  cache?: RequestCache;
}

export interface IApiResponse<T> {
  statusCode: number;
  errorMessage?: string;
  data?: T;
}
