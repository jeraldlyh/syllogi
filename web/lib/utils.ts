import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const cn = (...inputs: ClassValue[]): string => {
  return twMerge(clsx(inputs));
};

export const formatDateTime = (dateTime: string | null): string => {
  if (!dateTime) return "";

  const date = new Date(dateTime);

  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const capitaliseFirstLetter = (value: string): string => {
  return value.charAt(0).toUpperCase() + value.slice(1);
};

export const convertSnakeCaseToTitleCase = (value: string): string => {
  return value
    .split("_")
    .map((word) => capitaliseFirstLetter(word))
    .join(" ");
};
export const formatDuration = (seconds: number | null): string => {
  if (!seconds || seconds < 0) seconds = 0;

  const hour = Math.floor(seconds / 3600);
  const minute = Math.floor((seconds % 3600) / 60);
  const second = Math.floor(seconds % 60);

  if (hour > 0) return `${hour}h ${minute}m ${second}s`;
  if (minute > 0) return `${minute}m ${second}s`;
  return `${second}s`;
};

export const formatClock = (seconds: number): string => {
  if (!seconds || seconds < 0) return "--:--";

  const minutes = Math.floor(seconds / 60);
  const remainder = Math.floor(seconds % 60);

  return `${minutes}:${String(remainder).padStart(2, "0")}`;
};

export const formatSize = (bytes: number): string => {
  if (bytes >= 1_000_000) return `${(bytes / 1_048_576).toFixed(1)} MB`;
  return `${Math.round(bytes / 1024)} KB`;
};
