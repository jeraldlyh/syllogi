from fastapi import APIRouter

from db.sync_session import _get_sync_sessions, _get_sync_session_tracks
from db.session import SessionDep
from lib.utils import _format_time_with_locale

router = APIRouter()


@router.get(
    path="",
    summary="Get sync sessions",
    description="Retrieve a list of all sync sessions.",
)
async def get_sync_sessions(session: SessionDep):
    sync_sessions = _get_sync_sessions(session)

    tracks_by_session: dict[str, dict[str, list[str]]] = {
        str(sync_session.id): {"total": [], "new": [], "outdated": [], "missing": []}
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
        response.append(
            {
                "id": str(sync_session.id),
                "provider": sync_session.provider.value,
                "provider_playlist_id": sync_session.provider_playlist_id,
                "provider_playlist_name": sync_session.provider_playlist_name,
                "target_user_id": sync_session.target_user_id,
                "target_username": sync_session.target_username,
                "target_playlist_id": sync_session.target_playlist_id,
                "target_playlist_name": sync_session.target_playlist_name,
                "total_tracks": sync_session_tracks["total"],
                "new_tracks": sync_session_tracks["new"],
                "outdated_tracks": sync_session_tracks["outdated"],
                "missing_tracks": sync_session_tracks["missing"],
                "started_at": _format_time_with_locale(sync_session.started_at),
                "finished_at": _format_time_with_locale(sync_session.finished_at),
                "duration_seconds": sync_session.duration_seconds,
                "status": sync_session.status,
                "error_message": sync_session.error_message,
                "created_at": _format_time_with_locale(sync_session.created_at),
                "updated_at": _format_time_with_locale(sync_session.updated_at),
            }
        )

    return response
