import os
from difflib import SequenceMatcher

from lib.jellyfin import _search_jellyfin_songs
from lib.utils import _get_clean_name

CONFIDENCE_LEVEL = float(os.getenv("CONFIDENCE_LEVEL", "0.90"))


def _find_track(artist_name: str, track_name: str) -> dict:
    empty_result = {
        "artist_name": artist_name,
        "track": {"name": None, "id": None, "file_id": None},
        "album": {"name": None, "id": None},
        "search_name": track_name,
        "exists": False,
        "path": None,
        "quality": None,
    }

    tracks = _search_jellyfin_songs(artist_name=artist_name, title=track_name)
    best_match, best_score = None, 0.0

    for track in tracks:
        jellyfin_track_name = track.get("Name")
        clean_jellyfin_track_name = _get_clean_name(name=jellyfin_track_name)
        clean_search_track_name = _get_clean_name(name=track_name)

        if jellyfin_track_name.casefold() == track_name.casefold():
            return {
                "artist_name": artist_name,
                "track": {"id": track.get("Id"), "name": jellyfin_track_name},
                "album": {
                    "id": track.get("AlbumId"),
                    "name": track.get("Album"),
                },
                "search_name": track_name,
                "exists": True,
            }

        score = max(
            SequenceMatcher(
                None, clean_jellyfin_track_name, clean_search_track_name
            ).ratio(),
            SequenceMatcher(
                None, jellyfin_track_name.casefold(), track_name.casefold()
            ).ratio(),
        )
        if score >= CONFIDENCE_LEVEL and score > best_score:
            best_score = score
            best_match = track

    if best_match:
        return {
            "artist_name": artist_name,
            "track": {"id": best_match.get("Id"), "name": jellyfin_track_name},
            "album": {
                "id": best_match.get("AlbumId"),
                "name": best_match.get("Album"),
            },
            "search_name": track_name,
            "exists": True,
        }
    return empty_result
