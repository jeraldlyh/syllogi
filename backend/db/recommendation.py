import uuid
from typing import Sequence

from sqlmodel import select

from db.models.recommendation import (
    Recommendation,
)
from db.session import SessionDep


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
