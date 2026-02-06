from lib.lidarr import (
    _get_lidarr_artist,
    _get_potential_lidarr_songs,
    _get_lidarr_track_metadata,
)


def _find_track(artist_name: str, title: str) -> dict:
    empty_result = {
        "artist_name": artist_name,
        "track": {"name": None, "id": None, "file_id": None},
        "album": {"name": None, "id": None},
        "search_name": title,
        "exists": False,
        "path": None,
        "quality": None,
    }

    artist = _get_lidarr_artist(artist_name)

    if not artist:
        return empty_result

    artist_id = artist.get("id")
    candidates = _get_potential_lidarr_songs(title, artist_id)

    for candidate in candidates:
        if candidate.get("hasFile") and candidate.get("trackFileId"):
            file_meta = _get_lidarr_track_metadata(candidate.get("trackFileId"))

            return {
                "artist_name": artist_name,
                "track": {
                    "id": candidate.get("id"),
                    "name": candidate.get("title"),
                    "file_id": candidate.get("trackFileId"),
                },
                "album": {
                    "id": candidate.get("id"),
                    "name": candidate.get("album_name"),
                },
                "search_name": title,
                "exists": True,
                "path": file_meta.get("path"),
                "quality": file_meta.get("quality"),
            }
    return empty_result
