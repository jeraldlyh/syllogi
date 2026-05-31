import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query
from pydantic import BaseModel, Field

from lib.download import download_missing_tracks
from lib.lastfm import get_lastfm_chart_top_tracks
from lib.models.common import ExternalTrack
from lib.track import is_track_in_jellyfin

logger = logging.getLogger(__name__)

router = APIRouter()


class DownloadTrackRequest(BaseModel):
    artist_name: str = Field(min_length=1)
    track_name: str = Field(min_length=1)


@router.get(
    path="/trending",
    summary="Get trending tracks",
    description="Retrieve the current top trending tracks from Last.fm charts.",
    responses={
        200: {
            "description": "List of trending tracks retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "artist_name": "The Weeknd",
                            "track_name": "Blinding Lights",
                            "duration": 200,
                            "listeners": 5000000,
                            "playcount": 100000000,
                            "musicbrainz_id": "abc123",
                            "image_url": "https://lastfm.freetls.fastly.net/i/u/300x300/abc.jpg",
                            "exists": False,
                        }
                    ]
                }
            },
        }
    },
)
async def _get_trending_tracks(
    limit: Annotated[
        int, Query(description="Number of tracks to return", ge=1, le=100)
    ] = 50,
) -> list[dict]:
    tracks = await get_lastfm_chart_top_tracks(limit=limit)
    jellyfin_statuses = await asyncio.gather(
        *[is_track_in_jellyfin(track) for track in tracks]
    )
    return [
        {**track.to_dict(), "exists": exists}
        for track, exists in zip(tracks, jellyfin_statuses)
    ]


@router.post(
    path="/track",
    summary="Download a track",
    description="Trigger a background download for a single track by artist and title.",
    responses={
        200: {
            "description": "Download started successfully",
            "content": {
                "application/json": {"example": {"message": "Download started"}}
            },
        }
    },
)
async def _download_track(
    item: DownloadTrackRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    track = ExternalTrack(
        artist_name=item.artist_name,
        track_name=item.track_name,
    )
    background_tasks.add_task(download_missing_tracks, missing_tracks=[track])
    return {"message": "Download started"}
