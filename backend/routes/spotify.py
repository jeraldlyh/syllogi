import logging
from typing import Annotated, Any, Mapping

from fastapi import APIRouter, BackgroundTasks, HTTPException, Path
from pydantic import BaseModel

from db.models.playlist import Playlist
from db.models.sync_session import SyncProvider, SyncSession, SyncStatus
from db.playlist import _get_playlist_by_id
from db.session import SessionDep, get_isolated_session
from db.sync_session import _create_sync_session
from lib.spotify import (
    _get_spotify_playlist,
    _sync_spotify_playlist_task,
    _get_spotify_playlist_songs,
)
from lib.utils import _get_now

router = APIRouter()
logger = logging.getLogger(__name__)


class ImportPlaylist(BaseModel):
    playlist_id: str
    username: str


@router.get(
    path="/{id}",
    summary="Get playlist",
    description="Retrieve a Spotify playlist by its ID.",
)
def get_spotify_playlist(
    id: Annotated[str, Path(min_length=1, description="Spotify Playlist ID")],
) -> Mapping[str, Any]:
    playlist = _get_spotify_playlist(id)

    return playlist.to_dict()


@router.get(
    path="/{id}/songs",
    summary="Get Spotify playlist songs",
    description="Retrieve a Spotify playlist songs by its ID.",
)
def get_spotify_playlist_songs(
    id: Annotated[str, Path(min_length=1, description="Spotify Playlist ID")],
) -> list[dict[str, Any]]:
    songs = _get_spotify_playlist_songs(playlist_id=id)

    return [song.to_dict() for song in songs]


@router.post(
    path="/sync",
    summary="Sync playlist",
    description="Sync a Spotify playlist to Jellyfin.",
)
def sync_spotify_playlist(
    item: Playlist, background_tasks: BackgroundTasks
) -> dict[str, str]:
    session = get_isolated_session()
    playlist = _get_playlist_by_id(session=session, playlist_id=item.id)

    if not playlist:
        raise HTTPException(
            status_code=404, detail=f"Unable to find playlist: {item.playlist_id}"
        )

    playlist_id = playlist.playlist_id
    username = item.username
    started_at = _get_now()

    sync_session = SyncSession(
        provider=SyncProvider.spotify,
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
        _sync_spotify_playlist_task,
        playlist=playlist,
        sync_session=sync_session,
    )

    return {"id": str(sync_session.id)}
