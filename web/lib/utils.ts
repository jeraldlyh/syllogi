import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const cn = (...inputs: ClassValue[]): string => {
  return twMerge(clsx(inputs));
};

export const formatDateTime = (dateTime: string): string => {
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
export const formatDuration = (seconds: number): string => {
  if (seconds < 0) seconds = 0;

  const hour = Math.floor(seconds / 3600);
  const minute = Math.floor((seconds % 3600) / 60);
  const second = Math.floor(seconds % 60);

  if (hour > 0) return `${hour}h ${minute}m ${second}s`;
  if (minute > 0) return `${minute}m ${second}s`;
  return `${second}s`;
};
