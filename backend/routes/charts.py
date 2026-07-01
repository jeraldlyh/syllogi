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
from lib.providers.metadata.deezer import DeezerMetadataProvider
from lib.providers.metadata.musicbrainz import MusicBrainzMetadataProvider
from lib.providers.recommendation.lastfm import LastFMRecommendationProvider
from lib.track import find_track, is_track_in_provider

logger = logging.getLogger(__name__)

router = APIRouter()


class DownloadTrackRequest(BaseModel):
    artist_name: str = Field(min_length=1)
    track_name: str = Field(min_length=1)
    image_url: str = Field(default="", max_length=2048)


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
    deezer_provider = DeezerMetadataProvider()
    tracks = await LastFMRecommendationProvider().get_chart_top_tracks(limit=limit)

    deezer_tracks = await asyncio.gather(
        *[
            deezer_provider.get_artist_recording(
                artist_name=track.artist_name,
                track_name=track.track_name,
            )
            for track in tracks
        ]
    )

    for track, deezer_track in zip(tracks, deezer_tracks):
        if deezer_track and deezer_track.image_url:
            track.image_url = deezer_track.image_url

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
        album_name="",
        year="",
        duration=0,
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


@router.get(
    path="/artist/{artist_name}",
    summary="Get artist metadata",
    description="Retrieve artist metadata and recordings from MusicBrainz by artist name. Returns artist: null when not found.",
    responses={
        200: {
            "description": "Artist metadata (or null if not found)",
            "content": {
                "application/json": {
                    "examples": {
                        "found": {
                            "summary": "Artist found",
                            "value": {
                                "artist": {
                                    "id": "a74b1b7f-71a5-4028-9831-c43e3266b76e",
                                    "name": "Radiohead",
                                    "type": "Group",
                                    "country": "GB",
                                    "gender": "",
                                    "life_span": {
                                        "begin": "1985",
                                        "end": None,
                                    },
                                    "area": "United Kingdom",
                                    "begin_area": "Abingdon",
                                    "tags": [
                                        "alternative rock",
                                        "art rock",
                                        "electronic",
                                    ],
                                    "aliases": ["On a Friday"],
                                },
                                "recordings": [
                                    {
                                        "title": "Creep",
                                        "duration": 238,
                                        "exists": False,
                                    },
                                    {
                                        "title": "Karma Police",
                                        "duration": 264,
                                        "exists": True,
                                    },
                                ],
                            },
                        },
                        "not_found": {
                            "summary": "Artist not found",
                            "value": {"artist": None, "recordings": []},
                        },
                    },
                }
            },
        },
    },
)
async def _get_artist_info(
    artist_name: str,
    locale: str | None = Query(
        default=None,
        description="Browser locale (e.g. en-US, ja). Excludes aliases matching the user's language.",
    ),
) -> dict:
    mb_provider = MusicBrainzMetadataProvider()
    deezer_provider = DeezerMetadataProvider()

    artist_info = await mb_provider.get_artist_info(
        artist_name=artist_name, locale=locale
    )

    if not artist_info:
        return {"artist": None, "recordings": []}

    mb_recordings = await mb_provider.get_artist_recordings(artist_mbid=artist_info.id)
    deezer_info = await deezer_provider.get_artist_info(artist_name=artist_name)

    if deezer_info:
        artist_info.image_url = deezer_info.image_url
        artist_info.num_of_fans = deezer_info.num_of_fans

    deezer_tracks = await asyncio.gather(
        *[
            deezer_provider.get_artist_recording(
                artist_name=artist_name,
                track_name=recording.track_name,
            )
            for recording in mb_recordings
        ]
    )

    for recording, deezer_track in zip(mb_recordings, deezer_tracks):
        if deezer_track:
            recording.album_name = deezer_track.album_name

    provider = get_provider()

    track_existence = await asyncio.gather(
        *[
            find_track(
                provider=provider,
                artist_name=artist_name,
                track_name=recording.track_name,
                album_name="",
                year="",
                duration=recording.get_duration(),
            )
            for recording in mb_recordings
        ],
        return_exceptions=True,
    )

    return {
        "artist": artist_info.to_dict(),
        "recordings": [
            {
                "track_name": recording.track_name,
                "duration": recording.get_duration(),
                "exists": (
                    not provider_track.is_not_found()
                    if not isinstance(provider_track, BaseException)
                    else False
                ),
                "album_name": recording.album_name,
            }
            for recording, provider_track in zip(mb_recordings, track_existence)
        ],
    }
