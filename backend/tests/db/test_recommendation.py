import uuid

from sqlmodel import Session

from db.models.recommendation import (
    Recommendation,
    RecommendationProvider,
    RecommendationStrategy,
)
from db.recommendation import (
    create_recommendation,
    delete_recommendation,
    get_recommendation_by_id,
    get_recommendation_by_username,
    get_recommendations,
    update_recommendation,
)


def _make_recommendation(**overrides) -> Recommendation:
    defaults = {
        "username": "testuser",
        "provider": RecommendationProvider.lastfm,
        "strategy": RecommendationStrategy.top_tracks,
        "requested_count": 50,
        "cron_expression": "",
        "is_public": False,
        "playlist_name": "",
        "blend_users": None,
    }
    defaults.update(overrides)
    return Recommendation(**defaults)


class TestCreateRecommendation:
    def test_create(self, session: Session):
        recommendation = _make_recommendation()
        create_recommendation(session, recommendation)

        assert recommendation.id is not None


class TestGetRecommendations:
    def test_empty(self, session: Session):
        assert get_recommendations(session) == []

    def test_ordered_by_username(self, session: Session):
        create_recommendation(session, _make_recommendation(username="bob"))
        create_recommendation(session, _make_recommendation(username="alice"))

        recommendations = get_recommendations(session)

        assert recommendations[0].username == "alice"
        assert recommendations[1].username == "bob"


class TestGetRecommendationById:
    def test_found(self, session: Session):
        recommendation = _make_recommendation()
        create_recommendation(session, recommendation)

        assert get_recommendation_by_id(session, recommendation.id) is not None

    def test_not_found(self, session: Session):
        assert get_recommendation_by_id(session, uuid.uuid4()) is None


class TestGetRecommendationByUsername:
    def test_found(self, session: Session):
        create_recommendation(session, _make_recommendation(username="alice"))
        result = get_recommendation_by_username(session, "alice")

        assert result is not None

    def test_not_found(self, session: Session):
        assert get_recommendation_by_username(session, "nobody") is None


class TestUpdateRecommendation:
    def test_update(self, session: Session):
        recommendation = _make_recommendation()
        create_recommendation(session, recommendation)

        recommendation.requested_count = 100
        updated = update_recommendation(session, recommendation)

        assert updated.requested_count == 100


class TestDeleteRecommendation:
    def test_delete(self, session: Session):
        recommendation = _make_recommendation()

        create_recommendation(session, recommendation)
        delete_recommendation(session, recommendation)

        assert get_recommendation_by_id(session, recommendation.id) is None
