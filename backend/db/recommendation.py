import uuid
from db.models.recommendation import (
    RecommendationSession,
    RecommendationSessionTrack,
    RecommendationTrackType,
)
from db.session import SessionDep
from lib.common import LastFMRecentTrack, LastFMTopTrack


def create_recommendation_session(
    session: SessionDep, recommendation_session: RecommendationSession
) -> None:
    session.add(recommendation_session)
    session.commit()
    session.refresh(recommendation_session)


def update_recommendation_session(
    session: SessionDep, recommendation_session: RecommendationSession
) -> RecommendationSession:
    recommendation_session = session.merge(recommendation_session)
    session.commit()
    session.refresh(recommendation_session)
    return recommendation_session


def format_recommendation_session_track_names(
    tracks: list[LastFMTopTrack | LastFMRecentTrack],
) -> list[str]:
    return [f"{track.artist_name} - {track.track_name}" for track in tracks]


def build_recommendation_session_tracks(
    recommendation_session_id: uuid.UUID,
    names: list[str],
    type: RecommendationTrackType,
) -> list[RecommendationSessionTrack]:
    return [
        RecommendationSessionTrack(
            recommendation_session_id=recommendation_session_id, type=type, name=name
        )
        for name in names
    ]
