from typing import Any


from db.session import get_isolated_session
from lib.common import (
    LastFMRecentTrack,
    LastFMTopTrack,
)
from lib.lastfm import (
    get_lastfm_recent_tracks,
    get_lastfm_similar_tracks,
    get_lastfm_top_tracks,
)
from lib.track import find_track


def get_recommendations(user: str, num_recommendations: int = 50) -> Any:
    """Get track recommendations for a user based on their listening history."""

    with get_isolated_session() as session:
        recent_tracks = get_lastfm_recent_tracks(
            user=user, limit=round(num_recommendations * 0.7)
        )
        top_tracks = get_lastfm_top_tracks(
            user=user, limit=round(num_recommendations * 0.3)
        )
        all_tracks = recent_tracks + top_tracks
        missing_tracks: set[LastFMTopTrack | LastFMRecentTrack] = set()
        existing_tracks: set[LastFMTopTrack | LastFMRecentTrack] = set()

        for track in all_tracks:
            similar_tracks = get_lastfm_similar_tracks(
                user=user, artist=track.artist_name, track=track.track_name
            )

            for similar_track in similar_tracks:
                jellyfin_track = find_track(
                    artist_name=similar_track.artist_name,
                    track_name=similar_track.track_name,
                    album_name="",
                    year="",
                    duration=similar_track.duration,
                )

                if jellyfin_track.is_not_found():
                    missing_tracks.add(track)
                else:
                    existing_tracks.add(track)
                    break
        return {
            "existing_tracks": [track.to_dict() for track in existing_tracks],
            "missing_tracks": [track.to_dict() for track in missing_tracks],
        }
