import logging
from difflib import SequenceMatcher
from typing import Callable, TypeVar

from fastapi import HTTPException, status

from lib.jellyfin import search_jellyfin_track
from lib.models.common import (
    ExternalTrack,
    JellyfinTrack,
    ResolvedTrack,
)
from lib.models.lastfm import LastFMChartTrack
from lib.utils import get_clean_name, sanitize_filename

logger = logging.getLogger(__name__)
T = TypeVar("T")


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


async def find_track(
    artist_name: str, track_name: str, album_name: str, year: str, duration: int
) -> JellyfinTrack:
    """Find the best matching track in Jellyfin based on the provided metadata."""

    jellyfin_tracks = await search_jellyfin_track(
        artist_name=artist_name,
        title=sanitize_filename(name=track_name),
        album=album_name,
        year=year,
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
        return best_match
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


async def resolve_tracks(
    tracks: list[ExternalTrack],
) -> tuple[list[ResolvedTrack], list[ResolvedTrack]]:
    """Verifies which tracks from the source playlist can be found in the Jellyfin library.

    Returns (found_tracks, missing_tracks).
    """
    found: list[ResolvedTrack] = []
    missing: list[ResolvedTrack] = []

    for song in tracks:
        display_name = f"{song.artist_name} {song.album_name}: {song.track_name}"
        track = await find_track(
            artist_name=song.artist_name,
            track_name=song.track_name,
            album_name=song.album_name,
            year=song.year,
            duration=song.duration,
        )

        resolved = ResolvedTrack(
            track=song,
            jellyfin_id=track.id,
            display_name=display_name,
        )

        if track.is_not_found():
            logger.warning(f"{display_name}: MISSING")
            missing.append(resolved)
        else:
            logger.info(f"{display_name}: OK")
            found.append(resolved)

    return found, missing


def reconcile_after_download(
    found_tracks: list[T],
    found_tracks_after_download: list[ResolvedTrack],
    missing_tracks: list[T],
    missing_tracks_after_download: list[ExternalTrack],
    missing_tracks_after_scan: list[ResolvedTrack],
    get_key: Callable[[T], tuple[str, str]],
) -> tuple[list[T], list[T]]:
    """Update found/missing track lists after a download and rescan attempt.

    Builds a reverse lookup from the original missing tracks keyed by
    (artist_name, track_name), then:
    - Moves newly resolved tracks into found_tracks.
    - Rebuilds missing_tracks from tracks that still could not be found.

    Works generically over any track type T (e.g. ResolvedTrack, LastFMSimilarTrack)
    via the get_key callable, which extracts the (artist_name, track_name) pair from T.
    """

    initial_missing_map: dict[tuple[str, str], T] = {
        get_key(track): track for track in missing_tracks
    }

    updated_found: list[T] = list(found_tracks)

    for missing_track in found_tracks_after_download:
        key = (missing_track.track.artist_name, missing_track.track.track_name)
        original = initial_missing_map.get(key)

        if original:
            updated_found.append(original)

    updated_missing: list[T] = []

    for missing_track in missing_tracks_after_download:
        key = (missing_track.artist_name, missing_track.track_name)
        original = initial_missing_map.get(key)

        if original:
            updated_missing.append(original)

    for missing_track in missing_tracks_after_scan:
        key = (missing_track.track.artist_name, missing_track.track.track_name)
        original = initial_missing_map.get(key)

        if original:
            updated_missing.append(original)

    return updated_found, updated_missing


async def is_track_in_jellyfin(track: LastFMChartTrack) -> bool:
    """Return True if the track exists in the Jellyfin library, False otherwise."""
    try:
        jellyfin_track = await find_track(
            artist_name=track.artist_name,
            track_name=track.track_name,
            album_name="",
            year="",
            duration=track.duration,
        )
        return not jellyfin_track.is_not_found()
    except Exception:
        logger.warning(
            f"Failed to check Jellyfin for '{track.artist_name} - {track.track_name}'"
        )
        return False
