import uuid
from typing import Sequence

from sqlmodel import desc, select

from db.models.recommendation import (
    RecommendationSession,
    RecommendationSessionTrack,
    RecommendationTrackType,
)
from db.session import SessionDep
from lib.models.lastfm import LastFMSimilarTrack


def get_recommendation_sessions(session: SessionDep) -> Sequence[RecommendationSession]:
    return session.exec(
        select(RecommendationSession).order_by(desc(RecommendationSession.created_at))
    ).all()


def get_recommendation_session_tracks(
    session: SessionDep, recommendation_session_id: str | uuid.UUID
) -> Sequence[RecommendationSessionTrack]:
    return session.exec(
        select(RecommendationSessionTrack).where(
            RecommendationSessionTrack.recommendation_session_id
            == recommendation_session_id
        )
    ).all()


def get_recommendation_session_by_id(
    session: SessionDep, recommendation_session_id: str | uuid.UUID
) -> RecommendationSession | None:
    return session.get(RecommendationSession, recommendation_session_id)


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
    tracks: list[LastFMSimilarTrack],
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
