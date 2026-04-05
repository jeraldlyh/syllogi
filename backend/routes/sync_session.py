from fastapi import APIRouter

from db.sync_session import _get_sync_sessions, _get_sync_session_tracks
from db.session import SessionDep

router = APIRouter()


@router.get(
    path="",
    summary="Get sync sessions",
    description="Retrieve a list of all sync sessions.",
    responses={
        200: {
            "description": "Sync sessions retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "id": "473bce59-475e-4119-bf40-117d127f6e57",
                                "provider": "youtube",
                                "provider_playlist_id": "PL2veF8tRu_esmG6LMYKYdfby",
                                "provider_playlist_name": "The Daily Ketchup Podcast (TDK)",
                                "target_user_id": "3b1adf6f43734fb8a8b9c8e5d1a7c9e",
                                "target_username": "username",
                                "target_playlist_id": "c4f9ba0cb0c689e8b8a9d2e5f1a7c9e",
                                "target_playlist_name": "daily ketchup",
                                "started_at": "2026-04-04T23:09:53.181078+08:00",
                                "finished_at": "2026-04-04T23:10:22.417324+08:00",
                                "duration_seconds": 29,
                                "status": "completed",
                                "error_message": None,
                                "created_at": "2026-04-04T23:09:36.838593+08:00",
                                "updated_at": "2026-04-04T23:10:06.406705+08:00",
                                "total_tracks": ["Track A", "Track B"],
                                "new_tracks": ["Track A"],
                                "outdated_tracks": [],
                                "missing_tracks": [],
                                "downloaded_tracks": ["Track A"],
                            }
                        ],
                    }
                }
            },
        }
    },
)
def get_sync_sessions(session: SessionDep):
    sync_sessions = _get_sync_sessions(session)

    tracks_by_session: dict[str, dict[str, list[str]]] = {
        str(sync_session.id): {
            "total": [],
            "new": [],
            "outdated": [],
            "missing": [],
            "downloaded": [],
        }
        for sync_session in sync_sessions
    }

    for sync_session in sync_sessions:
        sync_session_id = sync_session.id
        session_tracks = _get_sync_session_tracks(
            session=session, sync_session_id=sync_session_id
        )
        for track in session_tracks:
            tracks_by_session[str(sync_session_id)][track.kind.value].append(track.name)

    response = []
    for sync_session in sync_sessions:
        sync_session_tracks = tracks_by_session[str(sync_session.id)]
        sync_session_dict = sync_session.to_dict()

        sync_session_dict["total_tracks"] = sync_session_tracks["total"]
        sync_session_dict["new_tracks"] = sync_session_tracks["new"]
        sync_session_dict["outdated_tracks"] = sync_session_tracks["outdated"]
        sync_session_dict["missing_tracks"] = sync_session_tracks["missing"]
        sync_session_dict["downloaded_tracks"] = sync_session_tracks["downloaded"]

        response.append(sync_session_dict)
    return response
