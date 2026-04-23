import uuid
from typing import Sequence

from sqlmodel import desc, select

from db.models.recommendation import (
    Recommendation,
    RecommendationSession,
    RecommendationSessionTrack,
    RecommendationTrackType,
)
from db.session import SessionDep
from lib.common import LastFMRecentTrack, LastFMTopTrack


def get_recommendations(session: SessionDep) -> Sequence[Recommendation]:
    return session.exec(select(Recommendation).order_by(Recommendation.username)).all()


def get_recommendation_by_id(
    session: SessionDep, recommendation_id: str | uuid.UUID
) -> Recommendation | None:
    return session.get(Recommendation, recommendation_id)


def get_recommendation_by_username(
    session: SessionDep, username: str
) -> Recommendation | None:
    return session.exec(
        select(Recommendation).where(Recommendation.username == username)
    ).first()


def create_recommendation(
    session: SessionDep, recommendation_setting: Recommendation
) -> None:
    session.add(recommendation_setting)
    session.commit()
    session.refresh(recommendation_setting)


def update_recommendation(
    session: SessionDep, recommendation_setting: Recommendation
) -> Recommendation:
    recommendation_setting = session.merge(recommendation_setting)
    session.commit()
    session.refresh(recommendation_setting)
    return recommendation_setting


def delete_recommendation(
    session: SessionDep, recommendation_setting: Recommendation
) -> None:
    session.delete(recommendation_setting)
    session.commit()


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
