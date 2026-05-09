import logging
from typing import Annotated, Any

from fastapi import APIRouter, Path
from pydantic import BaseModel

from lib.youtube import (
    get_youtube_playlist,
    get_youtube_playlist_songs,
    download_track_youtube,
)

router = APIRouter()
logger = logging.getLogger(__name__)


class DownloadYouTubeTrackRequest(BaseModel):
    artist_name: str
    track_name: str


@router.get(
    path="/{id}",
    summary="Get YouTube playlist",
    description="Retrieve a YouTube playlist by its ID.",
    responses={
        200: {
            "description": "YouTube playlist retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "id": "PL2veF8tRu_esmG6LMYKYdfby",
                            "name": "backup playlist",
                            "thumbnail_url": "https://example.com/thumbnail.jpg",
                            "total": 86,
                        },
                    }
                }
            },
        }
    },
)
def get_youtube_playlist(
    id: Annotated[str, Path(min_length=1, description="YouTube Playlist ID")],
) -> dict[str, Any]:
    playlist = get_youtube_playlist(id)

    return playlist.to_dict()


@router.get(
    path="/{id}/songs",
    summary="Get YouTube playlist songs",
    description="Retrieve a YouTube playlist songs by its ID.",
    responses={
        200: {
            "description": "YouTube playlist songs retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "artist_name": "Avicii",
                                "track_name": "Friend Of Mine (Original Video) ft. Vargas & Lagola",
                                "album_name": "",
                                "year": "",
                                "duration": 186,
                            }
                        ],
                    }
                }
            },
        }
    },
)
def get_youtube_playlist_songs(
    id: Annotated[str, Path(min_length=1, description="YouTube Playlist ID")],
) -> list[dict[str, Any]]:
    songs = get_youtube_playlist_songs(playlist_id=id)

    return [song.to_dict() for song in songs]


@router.post(
    path="/download",
    summary="Download YouTube playlist",
    description="Download songs from YouTube by its ID.",
    responses={
        200: {
            "description": "Track download status",
            "content": {
                "application/json": {
                    "example": {"success": True, "data": {"downloaded": True}}
                }
            },
        }
    },
)
async def _download_track(item: DownloadYouTubeTrackRequest) -> dict[str, bool]:
    is_downloaded = await download_track_youtube(
        artist_name=item.artist_name,
        track_name=item.track_name,
    )
    return {"downloaded": is_downloaded}
