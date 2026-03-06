import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from db.models.playlist import Playlist, PlaylistProvider
from db.models.sync_session import SyncProvider, SyncSession, SyncStatus
from db.playlist import _get_playlist_by_id
from db.session import get_isolated_session
from db.sync_session import _create_sync_session
from lib.common import ExternalPlaylist, Song
from lib.sync import _sync_playlist_task
from lib.spotify import (
    _get_spotify_playlist,
    _get_spotify_playlist_songs,
)
from lib.youtube import (
    _get_youtube_playlist,
    _get_youtube_playlist_songs,
)
from lib.utils import _get_now

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    path="/",
    summary="Sync playlist",
    description="Sync a playlist (Spotify/Youtube) to Jellyfin.",
)
def sync_playlist(item: Playlist, background_tasks: BackgroundTasks) -> dict[str, str]:
    session = get_isolated_session()
    internal_playlist = _get_playlist_by_id(session=session, playlist_id=item.id)

    if not internal_playlist:
        raise HTTPException(
            status_code=404, detail=f"Unable to find playlist: {item.playlist_id}"
        )

    songs: list[Song] = []
    external_playlist: ExternalPlaylist | None = None

    match internal_playlist.provider:
        case PlaylistProvider.spotify:
            songs = _get_spotify_playlist_songs(playlist_id=item.playlist_id)
            external_playlist = _get_spotify_playlist(playlist_id=item.playlist_id)
        case PlaylistProvider.youtube:
            songs = _get_youtube_playlist_songs(playlist_id=item.playlist_id)
            external_playlist = _get_youtube_playlist(playlist_id=item.playlist_id)

    playlist_id = internal_playlist.playlist_id
    username = item.username
    started_at = _get_now()

    sync_session = SyncSession(
        provider=SyncProvider(internal_playlist.provider.value),
        provider_playlist_id=playlist_id,
        provider_playlist_name="",
        target_user_id="",
        target_username=username,
        target_playlist_id="",
        target_playlist_name="",
        started_at=started_at,
        finished_at=started_at,
        duration_seconds=0,
        status=SyncStatus.pending,
    )
    _create_sync_session(session=session, sync_session=sync_session)
    background_tasks.add_task(
        _sync_playlist_task,
        internal_playlist=internal_playlist,
        external_playlist=external_playlist,
        songs=songs,
        sync_session=sync_session,
    )

    return {"id": str(sync_session.id)}
