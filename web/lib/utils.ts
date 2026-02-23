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
