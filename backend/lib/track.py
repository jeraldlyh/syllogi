from difflib import SequenceMatcher

from fastapi import HTTPException, status

from lib.models.common import (
    JellyfinTrack,
)
from lib.jellyfin import search_jellyfin_track
from lib.utils import get_clean_name


def normalize(text: str) -> str:
    """Normalize a name for comparison."""

    # text = re.compile(
    #     r"\s*[\(\[](remaster(ed)?|deluxe|bonus|feat\.?[^\)\]]*|live|remix|edition|version|anniversary|explicit)[\)\]]",
    #     re.IGNORECASE,
    # ).sub("", text)
    text = get_clean_name(name=text)
    return text.casefold().strip()


def _similarity_score(a: str, b: str) -> float:
    """Compare two strings using both raw and normalized forms."""

    norm_a, norm_b = normalize(a), normalize(b)

    if norm_a == norm_b:
        return 1.0

    return max(
        SequenceMatcher(None, norm_a, norm_b).ratio(),
        SequenceMatcher(None, a.casefold(), b.casefold()).ratio(),
    )


def _score_track(
    jellyfin_track: JellyfinTrack,
    artist_name: str,
    track_name: str,
    album_name: str,
    year: str,
    duration: int,
) -> float:
    """Score a track based on heuristic comparisons of its metadata against the provided metadata."""

    title_score = _similarity_score(jellyfin_track.track_name, track_name)

    artist_score = 0.0
    for artist in jellyfin_track.artists:
        artist_score = max(artist_score, _similarity_score(artist, artist_name))

    album_score = 0.0
    if album_name and jellyfin_track.album_name:
        album_score = _similarity_score(jellyfin_track.album_name, album_name)

    year_score = 0.0
    if year and str(jellyfin_track.year) == str(year):
        year_score = 1.0

    duration_score = 0.0
    if duration and jellyfin_track.duration_ticks:
        track_duration = jellyfin_track.duration_ticks / 10_000_000
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


def find_track(
    artist_name: str, track_name: str, album_name: str, year: str, duration: int
) -> JellyfinTrack:
    """Find the best matching track in Jellyfin based on the provided metadata."""

    jellyfin_tracks = search_jellyfin_track(
        artist_name=artist_name, title=track_name, album=album_name, year=year
    )
    best_match, best_score = None, 0.0

    for jellyfin_track in jellyfin_tracks:
        jellyfin_track_name = jellyfin_track.track_name

        if not jellyfin_track_name:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Missing Jellyfin track name",
            )

        score = _score_track(
            jellyfin_track=jellyfin_track,
            artist_name=artist_name,
            track_name=track_name,
            album_name=album_name,
            year=year,
            duration=duration,
        )
        if score > best_score:
            best_score = score
            best_match = jellyfin_track

    if best_match:
        return jellyfin_track
    return JellyfinTrack(
        id="",
        track_name=track_name,
        album_id="",
        album_name=album_name,
        musicbrainz_id="",
        artists=[],
        year=year,
        duration_ticks=0,
    )
