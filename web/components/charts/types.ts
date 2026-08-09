export type ViewMode = "list" | "grid";

export interface DownloadableTrack {
  artist_name: string;
  track_name: string;
  image_url: string;
  musicbrainz_id?: string;
}
