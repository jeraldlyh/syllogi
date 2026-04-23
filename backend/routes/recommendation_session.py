from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi import APIRouter

from db.recommendation import (
    get_recommendation_session_tracks,
    get_recommendation_sessions,
)
from db.session import SessionDep

router = APIRouter()


@router.get(
    path="",
    summary="Get recommendation sessions",
    description="Retrieve a list of all recommendation sessions.",
)
def _get_recommendation_sessions(session: SessionDep) -> list[dict]:
    recommendation_sessions = get_recommendation_sessions(session=session)

    tracks_by_session: dict[str, dict[str, list[str]]] = {
        str(recommendation_session.id): {
            "total": [],
            "matched": [],
            "missing": [],
            "downloaded": [],
        }
        for recommendation_session in recommendation_sessions
    }

    for recommendation_session in recommendation_sessions:
        recommendation_session_id = recommendation_session.id
        session_tracks = get_recommendation_session_tracks(
            session=session,
            recommendation_session_id=recommendation_session_id,
        )
        for track in session_tracks:
            tracks_by_session[str(recommendation_session_id)][track.type.value].append(
                track.name
            )

    response = []
    for recommendation_session in recommendation_sessions:
        recommendation_session_tracks = tracks_by_session[
            str(recommendation_session.id)
        ]
        recommendation_session_dict = recommendation_session.to_dict()

        recommendation_session_dict["total_tracks"] = recommendation_session_tracks[
            "total"
        ]
        recommendation_session_dict["matched_tracks"] = recommendation_session_tracks[
            "matched"
        ]
        recommendation_session_dict["missing_tracks"] = recommendation_session_tracks[
            "missing"
        ]
        recommendation_session_dict["downloaded_tracks"] = (
            recommendation_session_tracks["downloaded"]
        )

        response.append(recommendation_session_dict)

    return response
