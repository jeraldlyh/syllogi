import logging
from typing import Annotated, Any

from fastapi import APIRouter, Path
from pydantic import BaseModel

from lib.download import _download_track
from lib.youtube import _get_youtube_playlist, _get_youtube_playlist_songs

router = APIRouter()
logger = logging.getLogger(__name__)


class DownloadYouTubeTrackRequest(BaseModel):
    artist_name: str
    track_name: str
    enable_lyrics: bool


@router.get(
    path="/{id}",
    summary="Get YouTube playlist",
    description="Retrieve a YouTube playlist by its ID.",
)
def get_youtube_playlist(
    id: Annotated[str, Path(min_length=1, description="YouTube Playlist ID")],
) -> dict[str, Any]:
    playlist = _get_youtube_playlist(id)

    return playlist.to_dict()


@router.get(
    path="/{id}/songs",
    summary="Get YouTube playlist songs",
    description="Retrieve a YouTube playlist songs by its ID.",
)
def get_youtube_playlist_songs(
    id: Annotated[str, Path(min_length=1, description="YouTube Playlist ID")],
) -> list[dict[str, Any]]:
    songs = _get_youtube_playlist_songs(playlist_id=id)

    return [song.to_dict() for song in songs]


@router.post(
    path="/download",
    summary="Download YouTube playlist",
    description="Download songs from YouTube by its ID.",
)
async def download_track(item: DownloadYouTubeTrackRequest) -> dict[str, bool]:
    is_downloaded = _download_track(
        artist_name=item.artist_name,
        track_name=item.track_name,
        enable_lyrics=item.enable_lyrics,
    )
    return {"downloaded": is_downloaded}
