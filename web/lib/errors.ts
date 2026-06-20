import { ErrorResponse } from "./types";

export class ApiError extends Error {
  public readonly code: string;
  public readonly errorName: string;

  constructor(errorResponse: ErrorResponse) {
    super(errorResponse.message);

    this.name = "ApiError";
    this.code = errorResponse.code;
    this.errorName = errorResponse.name;
  }
}

export const formatErrorMessage = (error: unknown): string | undefined => {
  return error instanceof Error ? error.message : undefined;
};
