import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query
from pydantic import BaseModel, Field

from db.download_session import create_download_session, get_download_sessions
from db.models.download_session import DownloadSession, DownloadSessionStatus
from db.session import SessionDep
from lib.download import download_single_track
from lib.models.common import ExternalTrack
from lib.providers import get_provider
from lib.providers.lastfm import LastFMRecommendationProvider
from lib.track import is_track_in_provider

logger = logging.getLogger(__name__)

router = APIRouter()


class DownloadTrackRequest(BaseModel):
    artist_name: str = Field(min_length=1)
    track_name: str = Field(min_length=1)
    image_url: str = Field(min_length=1, max_length=2048)


@router.get(
    path="/trending",
    summary="Get trending tracks",
    description="Retrieve the current top trending tracks from Last.fm charts.",
    responses={
        200: {
            "description": "List of trending tracks retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
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
                        ],
                    }
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
    provider = get_provider()
    tracks = await LastFMRecommendationProvider().get_chart_top_tracks(limit=limit)

    provider_statuses = await asyncio.gather(
        *[is_track_in_provider(provider, track) for track in tracks]
    )
    return [
        {**track.to_dict(), "exists": exists}
        for track, exists in zip(tracks, provider_statuses)
    ]


@router.post(
    path="/track",
    summary="Download a track",
    description="Trigger a background download for a single track by artist and title.",
    responses={
        200: {
            "description": "Download started successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {"message": "Download started"},
                    }
                }
            },
        }
    },
)
async def _download_track(
    item: DownloadTrackRequest,
    background_tasks: BackgroundTasks,
    session: SessionDep,
) -> dict[str, str]:
    provider = get_provider()
    track = ExternalTrack(
        artist_name=item.artist_name,
        track_name=item.track_name,
    )
    download_session = DownloadSession(
        artist_name=item.artist_name,
        track_name=item.track_name,
        image_url=item.image_url,
        status=DownloadSessionStatus.pending,
    )
    create_download_session(session, download_session)
    background_tasks.add_task(
        download_single_track,
        download_session_id=download_session.id,
        track=track,
        provider=provider,
    )
    return {"message": "Download started"}


@router.get(
    path="/downloads",
    summary="Get chart downloads",
    description="Retrieve recent chart download requests and their statuses.",
    responses={
        200: {
            "description": "Chart downloads retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "id": "2baf7b6b-87de-4289-bdd8-42f138f8c9e1",
                                "artist_name": "The Weeknd",
                                "track_name": "Blinding Lights",
                                "status": "completed",
                            }
                        ],
                    }
                }
            },
        }
    },
)
async def _get_download_sessions(session: SessionDep) -> list[dict]:
    downloads = get_download_sessions(session, limit=20)
    return [download.to_dict() for download in downloads]
