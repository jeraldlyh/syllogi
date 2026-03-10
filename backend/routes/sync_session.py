from fastapi import APIRouter

from db.sync_session import _get_sync_sessions, _get_sync_session_tracks
from db.session import SessionDep

router = APIRouter()


@router.get(
    path="",
    summary="Get sync sessions",
    description="Retrieve a list of all sync sessions.",
)
def get_sync_sessions(session: SessionDep):
    sync_sessions = _get_sync_sessions(session)

    tracks_by_session: dict[str, dict[str, list[str]]] = {
        str(sync_session.id): {"total": [], "new": [], "outdated": [], "missing": [], "downloaded": []}
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
