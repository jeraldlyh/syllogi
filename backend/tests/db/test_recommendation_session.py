import uuid

from sqlmodel import Session

from db.models.recommendation import (
    RecommendationSession,
    RecommendationTrackType,
    RecommendationStatus,
    RecommendationProvider,
    RecommendationStrategy,
)
from db.recommendation_session import (
    build_recommendation_session_tracks,
    create_recommendation_session,
    format_recommendation_session_track_names,
    get_recommendation_session_by_id,
    get_recommendation_session_tracks,
    get_recommendation_sessions,
    update_recommendation_session,
)
from lib.models.common import RecommendationTrack


def _make_recommendation_session(**overrides) -> RecommendationSession:
    defaults = {
        "username": "testuser",
        "provider": RecommendationProvider.lastfm,
        "strategy": RecommendationStrategy.top_tracks,
        "requested_count": 50,
        "generated_count": 10,
        "blend_users": None,
        "duration_seconds": 15,
        "status": RecommendationStatus.completed,
    }
    defaults.update(overrides)
    return RecommendationSession(**defaults)


class TestCreateRecommendationSession:
    def test_create(self, session: Session):
        recommendation_session = _make_recommendation_session()
        create_recommendation_session(session, recommendation_session)

        assert recommendation_session.id is not None


class TestGetRecommendationSessionById:
    def test_found(self, session: Session):
        recommendation_session = _make_recommendation_session()
        create_recommendation_session(session, recommendation_session)

        assert (
            get_recommendation_session_by_id(session, recommendation_session.id)
            is not None
        )

    def test_not_found(self, session: Session):
        assert get_recommendation_session_by_id(session, uuid.uuid4()) is None


class TestGetRecommendationSessions:
    def test_empty(self, session: Session):
        assert get_recommendation_sessions(session) == []

    def test_returns_all(self, session: Session):
        create_recommendation_session(session, _make_recommendation_session())
        create_recommendation_session(session, _make_recommendation_session())

        assert len(get_recommendation_sessions(session)) == 2


class TestUpdateRecommendationSession:
    def test_update(self, session: Session):
        recommendation_session = _make_recommendation_session()
        create_recommendation_session(session, recommendation_session)

        recommendation_session.generated_count = 20
        updated = update_recommendation_session(session, recommendation_session)

        assert updated.generated_count == 20


class TestGetRecommendationSessionTracks:
    def test_empty(self, session: Session):
        assert get_recommendation_session_tracks(session, uuid.uuid4()) == []

    def test_returns_tracks(self, session: Session):
        recommendation_session = _make_recommendation_session()
        create_recommendation_session(session, recommendation_session)

        tracks = build_recommendation_session_tracks(
            recommendation_session.id,
            ["Track A", "Track B"],
            RecommendationTrackType.matched,
        )
        for track in tracks:
            session.add(track)

        session.commit()
        results = get_recommendation_session_tracks(session, recommendation_session.id)

        assert len(results) == 2


class TestBuildRecommendationSessionTracks:
    def test_builds_tracks(self):
        session_id = uuid.uuid4()
        tracks = build_recommendation_session_tracks(
            session_id, ["A", "B"], RecommendationTrackType.total
        )

        assert len(tracks) == 2
        assert all(t.recommendation_session_id == session_id for t in tracks)
        assert all(t.type == RecommendationTrackType.total for t in tracks)

    def test_empty_names(self):
        tracks = build_recommendation_session_tracks(
            uuid.uuid4(), [], RecommendationTrackType.total
        )
        assert tracks == []


class TestFormatRecommendationSessionTrackNames:
    def test_formats_names(self):
        tracks = [
            RecommendationTrack(
                artist_name="Artist A",
                track_name="Song 1",
                musicbrainz_id="",
                album_name="",
                year="",
                duration=0,
                playcount=0,
                similarity_score=0,
            ),
            RecommendationTrack(
                artist_name="Artist B",
                track_name="Song 2",
                musicbrainz_id="",
                album_name="",
                year="",
                duration=0,
                playcount=0,
                similarity_score=0,
            ),
        ]
        result = format_recommendation_session_track_names(tracks)

        assert result == ["Artist A - Song 1", "Artist B - Song 2"]

    def test_empty_list(self):
        assert format_recommendation_session_track_names([]) == []
