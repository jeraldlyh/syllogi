from difflib import SequenceMatcher

from fastapi import HTTPException, status

from lib.jellyfin import search_jellyfin_songs
from lib.utils import get_clean_name


def _normalize(text: str) -> str:
    """Normalize a name for comparison."""

    # text = re.compile(
    #     r"\s*[\(\[](remaster(ed)?|deluxe|bonus|feat\.?[^\)\]]*|live|remix|edition|version|anniversary|explicit)[\)\]]",
    #     re.IGNORECASE,
    # ).sub("", text)
    text = get_clean_name(name=text)
    return text.casefold().strip()


def _similarity_score(a: str, b: str) -> float:
    """Compare two strings using both raw and normalized forms."""

    norm_a, norm_b = _normalize(a), _normalize(b)

    if norm_a == norm_b:
        return 1.0

    return max(
        SequenceMatcher(None, norm_a, norm_b).ratio(),
        SequenceMatcher(None, a.casefold(), b.casefold()).ratio(),
    )


def _score_track(
    track: dict,
    artist_name: str,
    track_name: str,
    album_name: str,
    year: str,
    duration: int,
) -> float:
    """Score a track based on heuristic comparisons of its metadata against the provided metadata."""

    title_score = _similarity_score(track.get("Name", ""), track_name)

    artist_score = 0.0
    for artist in track.get("Artists", []):
        artist_score = max(artist_score, _similarity_score(artist, artist_name))

    album_score = 0.0
    if album_name and track.get("Album"):
        album_score = _similarity_score(track.get("Album", ""), album_name)

    year_score = 0.0
    if year and str(track.get("ProductionYear", "")) == str(year):
        year_score = 1.0

    duration_score = 0.0
    if duration and track.get("CumulativeRunTimeTicks"):
        track_duration = track.get("CumulativeRunTimeTicks", 0) / 10_000_000
        duration_difference = max(
            0.0, 1.0 - abs(track_duration - duration) / max(duration, track_duration)
        )
        duration_score = duration_difference if duration_difference > 0.85 else 0.0

    return (
        (title_score * 0.4)
        + (artist_score * 0.3)
        + (album_score * 0.1)
        + (year_score * 0.05)
        + (duration_score * 0.15)
    )


def _find_track(
    artist_name: str, track_name: str, album_name: str, year: str, duration: int
) -> dict:
    """Find the best matching track in Jellyfin based on the provided metadata."""

    empty_result = {
        "artist_name": artist_name,
        "track": {"name": None, "id": None, "file_id": None},
        "album": {"name": None, "id": None},
        "search_name": track_name,
        "exists": False,
        "path": None,
        "quality": None,
    }

    tracks = search_jellyfin_songs(
        artist=artist_name, title=track_name, album=album_name, year=year
    )
    best_match, best_score = None, 0.0

    for track in tracks:
        jellyfin_track_name = track.get("Name")

        if not jellyfin_track_name:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Missing Jellyfin track name",
            )

        score = _score_track(
            track=track,
            artist_name=artist_name,
            track_name=track_name,
            album_name=album_name,
            year=year,
            duration=duration,
        )
        if score > best_score:
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
