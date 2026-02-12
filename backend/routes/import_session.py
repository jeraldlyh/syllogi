from fastapi import APIRouter

from db.import_session import _get_import_sessions, _get_import_session_tracks
from db.session import SessionDep

router = APIRouter()


@router.get(path="")
async def get_import_sessions(session: SessionDep):
    import_sessions = _get_import_sessions(session)

    tracks_by_session: dict[str, dict[str, list[str]]] = {
        str(import_session.id): {"total": [], "new": [], "outdated": [], "missing": []}
        for import_session in import_sessions
    }

    for import_session in import_sessions:
        import_session_id = import_session.id
        session_tracks = _get_import_session_tracks(
            session=session, import_session_id=import_session_id
        )
        for track in session_tracks:
            tracks_by_session[str(import_session_id)][track.kind.value].append(
                track.name
            )

    response = []
    for import_session in import_sessions:
        import_session_tracks = tracks_by_session[str(import_session.id)]
        response.append(
            {
                "id": str(import_session.id),
                "provider": import_session.provider.value,
                "provider_playlist_id": import_session.provider_playlist_id,
                "provider_playlist_name": import_session.provider_playlist_name,
                "target_user_id": import_session.target_user_id,
                "target_username": import_session.target_username,
                "target_playlist_id": import_session.target_playlist_id,
                "target_playlist_name": import_session.target_playlist_name,
                "total_tracks": import_session_tracks["total"],
                "new_tracks": import_session_tracks["new"],
                "outdated_tracks": import_session_tracks["outdated"],
                "missing_tracks": import_session_tracks["missing"],
                "started_at": import_session.started_at,
                "finished_at": import_session.finished_at,
                "duration_seconds": import_session.duration_seconds,
                "success": import_session.success,
                "error_message": import_session.error_message,
                "created_at": import_session.created_at,
                "updated_at": import_session.updated_at,
            }
        )

    return response
