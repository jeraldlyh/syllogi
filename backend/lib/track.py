import logging
from difflib import SequenceMatcher
from typing import Callable, TypeVar

from lib.models.common import (
    ExternalTrack,
    ResolvedTrack,
)
from lib.models.lastfm import LastFMChartTrack
from lib.models.provider import ProviderTrack
from lib.providers.playlist.base import MusicPlaylistProvider
from lib.utils import get_clean_name

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
    track: ProviderTrack,
    artist_name: str,
    track_name: str,
    album_name: str,
    year: str,
    duration: int,
) -> float:
    """Score a track based on heuristic comparisons of its metadata against the provided metadata."""

    title_score = _similarity_score(track.track_name, track_name)

    artist_score = 0.0
    for artist in track.artists:
        artist_score = max(artist_score, _similarity_score(artist, artist_name))

    album_score = 0.0
    if album_name and track.album_name:
        album_score = _similarity_score(track.album_name, album_name)

    year_score = 0.0
    if year and str(track.year) == str(year):
        year_score = 1.0

    duration_score = 0.0
    if duration and track.duration_ticks:
        track_duration = track.duration_ticks / 10_000_000
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


MIN_MATCH_SCORE = 0.5


async def find_track(
    provider: MusicPlaylistProvider,
    artist_name: str,
    track_name: str,
    album_name: str,
    year: str,
    duration: int,
) -> ProviderTrack:
    """Find the best matching track in the music provider based on the provided metadata."""

    provider_tracks = await provider.search_track(
        artist_name=artist_name,
        title=track_name,
        album=album_name,
        year=year,
    )
    best_match, best_score = None, 0.0

    for provider_track in provider_tracks:
        jellyfin_track_name = provider_track.track_name

        if not jellyfin_track_name:
            logger.warning(
                f"Skipping track with missing name: {artist_name} {album_name})"
            )
            continue

        score = _score_track(
            track=provider_track,
            artist_name=artist_name,
            track_name=track_name,
            album_name=album_name,
            year=year,
            duration=duration,
        )
        if score > best_score:
            best_score = score
            best_match = provider_track

    if best_match and best_score >= MIN_MATCH_SCORE:
        return best_match
    return ProviderTrack(
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
    provider: MusicPlaylistProvider,
    tracks: list[ExternalTrack],
) -> tuple[list[ResolvedTrack], list[ResolvedTrack]]:
    """Verifies which tracks from the source playlist can be found in the provider library.

    Returns (found_tracks, missing_tracks).
    """
    found: list[ResolvedTrack] = []
    missing: list[ResolvedTrack] = []

    for song in tracks:
        display_name = f"{song.artist_name} {song.album_name}: {song.track_name}"
        track = await find_track(
            provider=provider,
            artist_name=song.artist_name,
            track_name=song.track_name,
            album_name=song.album_name,
            year=song.year,
            duration=song.duration,
        )

        resolved = ResolvedTrack(
            track=song,
            provider_track_id=track.id,
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

    Works generically over any track type T (e.g. ResolvedTrack)
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


async def is_track_in_provider(
    provider: MusicPlaylistProvider, track: LastFMChartTrack
) -> bool:
    """Return True if the track exists in the provider library, False otherwise."""

    try:
        provider_track = await find_track(
            provider=provider,
            artist_name=track.artist_name,
            track_name=track.track_name,
            album_name="",
            year="",
            duration=track.duration,
        )
        return not provider_track.is_not_found()
    except Exception:
        logger.warning(
            f"Failed to check provider for '{track.artist_name} - {track.track_name}'"
        )
        return False
