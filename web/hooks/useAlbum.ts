import { fetcher } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import useSWR from "swr";
import { ArtistTrack } from "./useArtist";

export interface AlbumInfo {
  title: string;
  artist_name: string;
  image_url: string;
  release_date: string;
}

export interface AlbumData {
  album: AlbumInfo | null;
  tracks: ArtistTrack[];
}

export const useAlbum = (
  artistName: string | null,
  albumName: string | null,
) => {
  const { data, error, isLoading } = useSWR<ApiResponse<AlbumData>>(
    artistName && albumName
      ? `/charts/album?artist_name=${encodeURIComponent(artistName)}&album_name=${encodeURIComponent(albumName)}`
      : null,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    },
  );

  return {
    data: data?.data,
    isLoading,
    isError: error,
  };
};
