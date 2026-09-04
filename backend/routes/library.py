import logging
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from mutagen import MutagenError
from pydantic import BaseModel, Field

from db.library import (
    get_duplicate_tracks,
    get_empty_folders,
    query_tracks,
    summarize_library,
    upsert_tracks,
)
from db.session import SessionDep
from lib.library import (
    delete_empty_folders,
    delete_library_tracks,
    get_library_directory,
    get_scan_state,
    read_library_track,
    resolve_library_path,
    trigger_library_sweep,
)
from lib.models.library import AudioTags
from lib.providers import get_provider
from lib.providers.lyrics.lrclib import LRCLIBLyricsProvider
from lib.providers.metadata.musicbrainz import MusicBrainzMetadataProvider
from lib.tagger import get_tag_frames, write_audio_tags

logger = logging.getLogger(__name__)

router = APIRouter()


class DeleteTracksRequest(BaseModel):
    paths: list[Annotated[str, Field(min_length=1, max_length=4096)]] = Field(
        min_length=1, max_length=500
    )


class UpdateTagsRequest(BaseModel):
    path: str = Field(min_length=1, max_length=4096)
    title: str = Field(default="", max_length=512)
    artist: str = Field(default="", max_length=512)
    album: str = Field(default="", max_length=512)
    date: str = Field(default="", max_length=32)
    genres: list[str] = Field(default_factory=list, max_length=32)
    lyrics: str = Field(default="", max_length=65536)
    musicbrainz_id: str = Field(default="", max_length=64)


@router.get(
    path="/tracks",
    summary="List library files",
    description="Scan the download directory and return every audio file with the tags it carries.",
    responses={
        200: {
            "description": "Library files retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "directory": "/downloads",
                            "scanning": False,
                            "last_scanned_at": "2026-09-01T13:46:02+08:00",
                            "error": None,
                            "summary": {
                                "total": 412,
                                "missing_lyrics": 96,
                                "missing_musicbrainz_id": 210,
                                "lossless": 188,
                                "duplicates": 14,
                                "empty_directories": 3,
                            },
                            "matched": 412,
                            "tracks": [
                                {
                                    "path": "The Weeknd/After Hours/Blinding Lights.flac",
                                    "filename": "Blinding Lights.flac",
                                    "directory": "The Weeknd/After Hours",
                                    "format": "flac",
                                    "size": 32145678,
                                    "duration": 200,
                                    "has_lyrics": True,
                                    "is_synced_lyrics": True,
                                    "filled_fields": ["title", "artist", "album"],
                                    "tags": {
                                        "title": "Blinding Lights",
                                        "artist": "The Weeknd",
                                        "album": "After Hours",
                                        "date": "2020",
                                        "genres": ["synth-pop"],
                                        "musicbrainz_id": "",
                                    },
                                }
                            ],
                        },
                    }
                }
            },
        }
    },
)
def _list_library_tracks(
    session: SessionDep,
    q: Annotated[
        str, Query(description="Filter by file name, title, artist or album")
    ] = "",
    file_format: Annotated[
        Literal["", "flac", "mp3", "opus"], Query(description="Filter by container")
    ] = "",
    missing: Annotated[
        Literal["", "lyrics", "musicbrainz_id", "any"],
        Query(description="Only return files missing this tag"),
    ] = "",
    limit: Annotated[
        int, Query(description="Number of files to return", ge=1, le=500)
    ] = 100,
    offset: Annotated[int, Query(description="Number of files to skip", ge=0)] = 0,
) -> dict:
    trigger_library_sweep()

    tracks, matched = query_tracks(
        session,
        query=q,
        file_format=file_format,
        missing=missing,
        limit=limit,
        offset=offset,
    )

    return {
        "directory": str(get_library_directory()),
        **get_scan_state(),
        "summary": summarize_library(session),
        "matched": matched,
        "tracks": [track.to_dict() for track in tracks],
    }


@router.post(
    path="/scan",
    summary="Rescan the library",
    description=(
        "Start a sweep of the download directory in the background. Returns immediately; "
        "poll the track list to watch `scanning` clear as the sweep lands."
    ),
    responses={
        200: {
            "description": "Scan state reported successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "started": True,
                            "scanning": True,
                            "last_scanned_at": "2026-09-01T13:46:02+08:00",
                            "error": None,
                        },
                    }
                }
            },
        }
    },
)
async def _scan_library(
    force: Annotated[
        bool, Query(description="Sweep even if the last one is still fresh")
    ] = True,
) -> dict:
    return {"started": trigger_library_sweep(force=force), **get_scan_state()}


@router.get(
    path="/folders",
    summary="List empty folders",
    description=(
        "Return the folders the last sweep found holding no audio. Only the outermost "
        "one is listed: an artist folder of empty album folders counts once."
    ),
    responses={
        200: {
            "description": "Empty folders retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {"path": "The Weeknd/After Hours"},
                            {"path": "Daft Punk"},
                        ],
                    }
                }
            },
        }
    },
)
def _list_empty_folders(session: SessionDep) -> list[dict]:
    return [folder.to_dict() for folder in get_empty_folders(session)]


@router.delete(
    path="/folders",
    summary="Delete every empty folder",
    description=(
        "Delete the folders holding no audio, along with any non-audio leftovers inside them."
    ),
    responses={
        200: {
            "description": "Empty folders deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "deleted": ["The Weeknd/After Hours", "Daft Punk"],
                            "kept": [],
                        },
                    }
                }
            },
        }
    },
)
def _delete_empty_folders(session: SessionDep) -> dict:
    return delete_empty_folders(session)


@router.get(
    path="/duplicates",
    summary="List duplicated tracks",
    description=(
        "Return the tracks the library holds more than one file for, grouped by the "
        "recording they share. Files are matched on artist and title, falling back to "
        "the folder and file name when a file carries no title."
    ),
    responses={
        200: {
            "description": "Duplicated tracks retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "title": "Blinding Lights",
                                "artist": "The Weeknd",
                                "tracks": [
                                    {
                                        "path": "The Weeknd/After Hours/Blinding Lights.flac",
                                        "filename": "Blinding Lights.flac",
                                        "directory": "The Weeknd/After Hours",
                                        "format": "flac",
                                        "size": 32145678,
                                        "duration": 200,
                                        "has_lyrics": True,
                                        "is_synced_lyrics": True,
                                        "filled_fields": ["title", "artist", "album"],
                                        "tags": {
                                            "title": "Blinding Lights",
                                            "artist": "The Weeknd",
                                            "album": "After Hours",
                                            "date": "2020",
                                            "genres": ["synth-pop"],
                                            "musicbrainz_id": "",
                                        },
                                    }
                                ],
                            }
                        ],
                    }
                }
            },
        }
    },
)
def _list_duplicate_tracks(session: SessionDep) -> list[dict]:
    return [
        {
            "title": group[0].title or group[0].filename,
            "artist": group[0].artist,
            "tracks": [track.to_dict() for track in group],
        }
        for group in get_duplicate_tracks(session)
    ]


@router.delete(
    path="/tracks",
    summary="Delete library files",
    description=(
        "Delete the named audio files from disk and drop them from the library, then "
        "trigger a music server rescan. A file already gone is reported as deleted."
    ),
    responses={
        200: {
            "description": "Files deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "deleted": ["The Weeknd/After Hours/Blinding Lights.opus"],
                            "kept": [],
                        },
                    }
                }
            },
        }
    },
)
def _delete_library_tracks(
    session: SessionDep,
    item: DeleteTracksRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    result = delete_library_tracks(session, item.paths)

    if result["deleted"]:
        background_tasks.add_task(get_provider().rescan_library)

    return result


@router.get(
    path="/track",
    summary="Get a library file",
    description="Read the full tag set of a single audio file, including its lyrics.",
    responses={
        200: {
            "description": "File tags retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "path": "The Weeknd/After Hours/Blinding Lights.flac",
                            "frames": {
                                "title": "TITLE",
                                "artist": "ARTIST",
                                "album": "ALBUM",
                                "date": "DATE",
                                "genres": "GENRE",
                                "lyrics": "LYRICS",
                                "musicbrainz_id": "MUSICBRAINZ_TRACKID",
                            },
                            "tags": {
                                "title": "Blinding Lights",
                                "artist": "The Weeknd",
                                "album": "After Hours",
                                "date": "2020",
                                "genres": ["synth-pop"],
                                "lyrics": "[00:00.00] ...",
                                "musicbrainz_id": "",
                            },
                        },
                    }
                }
            },
        }
    },
)
def _get_library_track(
    session: SessionDep,
    path: Annotated[str, Query(description="File path relative to the library root")],
) -> dict:
    file_path = resolve_library_path(path)
    result = read_library_track(file_path)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to read tags from {path}",
        )

    track, lyrics = result
    upsert_tracks(session, [track])

    return {
        **track.to_dict(lyrics=lyrics),
        "frames": get_tag_frames(str(file_path)),
    }


@router.put(
    path="/track",
    summary="Update a library file's tags",
    description=(
        "Write the submitted tags to the audio file and trigger a music server rescan. "
        "Every field is written, so a field submitted empty clears that tag on disk."
    ),
    responses={
        200: {
            "description": "Tags written successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "path": "The Weeknd/After Hours/Blinding Lights.flac",
                            "tags": {"title": "Blinding Lights"},
                        },
                    }
                }
            },
        }
    },
)
def _update_library_track(
    session: SessionDep,
    item: UpdateTagsRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    file_path = resolve_library_path(item.path)

    try:
        write_audio_tags(
            file_path=str(file_path),
            tags=AudioTags(
                title=item.title.strip(),
                artist=item.artist.strip(),
                album=item.album.strip(),
                date=item.date.strip(),
                genres=[genre.strip() for genre in item.genres if genre.strip()],
                lyrics=item.lyrics.strip(),
                musicbrainz_id=item.musicbrainz_id.strip(),
            ),
        )
    except (MutagenError, OSError, ValueError) as e:
        logger.error(f"Failed to write tags to {item.path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to write tags to {item.path}",
        )

    result = read_library_track(file_path)
    provider = get_provider()

    background_tasks.add_task(provider.rescan_library)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to read tags from {item.path}",
        )

    track, lyrics = result
    upsert_tracks(session, [track])

    return {
        **track.to_dict(lyrics=lyrics),
        "frames": get_tag_frames(str(file_path)),
    }


@router.get(
    path="/lyrics",
    summary="Search LRCLIB for lyrics",
    description="Find lyrics candidates for a track. Synced lyrics carry LRC timestamps.",
    responses={
        200: {
            "description": "Lyrics candidates retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "id": 3396226,
                                "track_name": "Blinding Lights",
                                "artist_name": "The Weeknd",
                                "album_name": "After Hours",
                                "duration": 200,
                                "instrumental": False,
                                "plain_lyrics": "Yeah...",
                                "synced_lyrics": "[00:00.00] Yeah...",
                            }
                        ],
                    }
                }
            },
        }
    },
)
async def _search_lyrics(
    track_name: Annotated[str, Query(description="Track title", max_length=200)] = "",
    artist_name: Annotated[str, Query(description="Artist name", max_length=200)] = "",
    album_name: Annotated[str, Query(description="Album name", max_length=200)] = "",
    q: Annotated[
        str, Query(description="Free-text search, used instead of the fields above")
    ] = "",
) -> list[dict]:
    if not q and not track_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide a track name or a search query",
        )

    candidates = await LRCLIBLyricsProvider().search_lyrics(
        query=q,
        track_name=track_name,
        artist_name=artist_name,
        album_name=album_name,
    )
    return [candidate.to_dict() for candidate in candidates]


@router.get(
    path="/recordings",
    summary="Search MusicBrainz recordings",
    description="Find MusicBrainz recordings for a track, so one can be linked to the file.",
    responses={
        200: {
            "description": "Recordings retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "id": "9b1a2b3c-4d5e-6f70-8192-a3b4c5d6e7f8",
                                "title": "Blinding Lights",
                                "artist_name": "The Weeknd",
                                "album_name": "After Hours",
                                "release_date": "2020-03-20",
                                "year": "2020",
                                "duration": 200,
                                "disambiguation": "",
                                "genres": ["synth-pop"],
                                "score": 100,
                                "url": "https://musicbrainz.org/recording/9b1a2b3c-4d5e-6f70-8192-a3b4c5d6e7f8",
                            }
                        ],
                    }
                }
            },
        }
    },
)
async def _search_recordings(
    track_name: Annotated[str, Query(description="Track title", max_length=200)] = "",
    artist_name: Annotated[str, Query(description="Artist name", max_length=200)] = "",
    album_name: Annotated[str, Query(description="Album name", max_length=200)] = "",
    q: Annotated[
        str, Query(description="Free-text search, used instead of the fields above")
    ] = "",
    limit: Annotated[
        int, Query(description="Number of recordings to return", ge=1, le=25)
    ] = 10,
) -> list[dict]:
    if not q and not track_name and not artist_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide a track name, an artist name, or a search query",
        )

    matches = await MusicBrainzMetadataProvider().search_tracks(
        query=q,
        track_name=track_name,
        artist_name=artist_name,
        album_name=album_name,
        limit=limit,
    )
    return [
        {
            **match.to_search_dict(),
            "url": f"https://musicbrainz.org/recording/{match.id}",
        }
        for match in matches
    ]
