import uuid
from typing import Sequence

from sqlmodel import desc, select

from db.models.recommendation import (
    RecommendationSession,
    RecommendationSessionTrack,
    RecommendationSetting,
    RecommendationTrackType,
)
from db.session import SessionDep
from lib.common import LastFMRecentTrack, LastFMTopTrack


def get_recommendation_setting_by_username(
    session: SessionDep, username: str
) -> RecommendationSetting | None:
    return session.exec(
        select(RecommendationSetting).where(RecommendationSetting.username == username)
    ).first()


def create_recommendation_setting(
    session: SessionDep, recommendation_setting: RecommendationSetting
) -> None:
    session.add(recommendation_setting)
    session.commit()
    session.refresh(recommendation_setting)


def update_recommendation_setting(
    session: SessionDep, recommendation_setting: RecommendationSetting
) -> RecommendationSetting:
    recommendation_setting = session.merge(recommendation_setting)
    session.commit()
    session.refresh(recommendation_setting)
    return recommendation_setting


def get_recommendation_sessions(session: SessionDep) -> Sequence[RecommendationSession]:
    return session.exec(
        select(RecommendationSession).order_by(desc(RecommendationSession.created_at))
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
