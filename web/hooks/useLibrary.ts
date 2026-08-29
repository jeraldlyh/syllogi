import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import { useEffect, useState } from "react";
import useSWR from "swr";

export const TAG_FIELDS = [
  "title",
  "artist",
  "album",
  "date",
  "genres",
  "lyrics",
  "musicbrainz_id",
] as const;

export type TagField = (typeof TAG_FIELDS)[number];

export const TAG_FIELD_LABELS: Record<TagField, string> = {
  title: "Title",
  artist: "Artist",
  album: "Album",
  date: "Date",
  genres: "Genre",
  lyrics: "Lyrics",
  musicbrainz_id: "Recording",
};

export type LibraryFormat = "flac" | "mp3" | "opus";

export type TagSource = "file" | "musicbrainz" | "lrclib" | "you";

export interface AudioTags {
  title: string;
  artist: string;
  album: string;
  date: string;
  genres: string[];
  lyrics: string;
  musicbrainz_id: string;
}

export interface LibraryTrack {
  path: string;
  filename: string;
  directory: string;
  format: LibraryFormat;
  size: number;
  duration: number;
  has_lyrics: boolean;
  is_synced_lyrics: boolean;
  filled_fields: TagField[];
  tags: Omit<AudioTags, "lyrics">;
}

export interface LibraryTrackDetail extends Omit<LibraryTrack, "tags"> {
  tags: AudioTags;
  frames: Record<TagField, string>;
}

export interface LibrarySummary {
  total: number;
  missing_lyrics: number;
  missing_musicbrainz_id: number;
  lossless: number;
}

export interface LibraryResponse {
  directory: string;
  summary: LibrarySummary;
  matched: number;
  tracks: LibraryTrack[];
}

export interface LyricsCandidate {
  id: number;
  track_name: string;
  artist_name: string;
  album_name: string;
  duration: number;
  instrumental: boolean;
  plain_lyrics: string;
  synced_lyrics: string;
}

export interface RecordingMatch {
  id: string;
  title: string;
  artist_name: string;
  album_name: string;
  release_date: string;
  year: string;
  duration: number;
  disambiguation: string;
  genres: string[];
  score: number;
  url: string;
}

export interface LibraryFilters {
  query: string;
  format: LibraryFormat | "";
  missing: "" | "lyrics" | "musicbrainz_id" | "any";
}

export const LIBRARY_PAGE_SIZE = 100;

export const SEARCH_DEBOUNCE_MS = 300;

const useDebounced = <T>(value: T, delay: number): T => {
  const [settled, setSettled] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setSettled(value), delay);

    return () => clearTimeout(timer);
  }, [value, delay]);

  return settled;
};

export const useLibraryTracks = (filters: LibraryFilters) => {
  const query = useDebounced(filters.query, SEARCH_DEBOUNCE_MS);
  const params = new URLSearchParams({ limit: String(LIBRARY_PAGE_SIZE) });

  if (query.trim()) params.set("q", query.trim());
  if (filters.format) params.set("file_format", filters.format);
  if (filters.missing) params.set("missing", filters.missing);

  const { data, error, isLoading, mutate } = useSWR<
    ApiResponse<LibraryResponse>
  >(`/library/tracks?${params.toString()}`, fetcher, {
    keepPreviousData: true,
    revalidateOnFocus: false,
  });

  return {
    data: data?.data,
    isLoading,
    isError: error,
    refresh: mutate,
  };
};

export const useLibraryTrack = (path: string | null) => {
  const { data, error, isLoading, mutate } = useSWR<
    ApiResponse<LibraryTrackDetail>
  >(path ? `/library/track?path=${encodeURIComponent(path)}` : null, fetcher, {
    revalidateOnFocus: false,
  });

  return {
    data: data?.data,
    isLoading,
    isError: error,
    refresh: mutate,
  };
};

export const useRecordingMatches = (query: string | null) => {
  const { data, error, isLoading } = useSWR<ApiResponse<RecordingMatch[]>>(
    query ? `/library/recordings?q=${encodeURIComponent(query)}` : null,
    fetcher,
    { revalidateOnFocus: false, keepPreviousData: true },
  );

  return {
    data: data?.data,
    isLoading: Boolean(query) && isLoading,
    isError: error,
  };
};

export const useLyricsCandidates = (query: string | null) => {
  const { data, error, isLoading } = useSWR<ApiResponse<LyricsCandidate[]>>(
    query ? `/library/lyrics?q=${encodeURIComponent(query)}` : null,
    fetcher,
    { revalidateOnFocus: false, keepPreviousData: true },
  );

  return {
    data: data?.data,
    isLoading: Boolean(query) && isLoading,
    isError: error,
  };
};
