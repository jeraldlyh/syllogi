import uuid

from sqlmodel import Session

from db.download_session import (
    create_download_session,
    get_download_session_by_id,
    get_download_sessions,
    update_download_session,
)
from db.models.download_session import DownloadSession, DownloadSessionStatus


def _make_download_session(**overrides) -> DownloadSession:
    defaults = {
        "artist_name": "Test Artist",
        "track_name": "Test Track",
        "image_url": "https://example.com/img.jpg",
        "status": DownloadSessionStatus.pending,
    }
    defaults.update(overrides)
    return DownloadSession(**defaults)


class TestCreateDownloadSession:
    def test_create(self, session: Session):
        download = _make_download_session()
        result = create_download_session(session, download)

        assert result.id is not None

    def test_create_returns_object(self, session: Session):
        download = _make_download_session()
        result = create_download_session(session, download)
        assert result.artist_name == "Test Artist"


class TestGetDownloadSessionById:
    def test_found(self, session: Session):
        download = _make_download_session()
        create_download_session(session, download)
        assert get_download_session_by_id(session, download.id) is not None

    def test_not_found(self, session: Session):
        assert get_download_session_by_id(session, uuid.uuid4()) is None


class TestGetDownloadSessions:
    def test_empty(self, session: Session):
        assert get_download_sessions(session) == []

    def test_respects_limit(self, session: Session):
        for i in range(5):
            create_download_session(
                session, _make_download_session(track_name=f"Track {i}")
            )
        assert len(get_download_sessions(session, limit=3)) == 3

    def test_default_limit(self, session: Session):
        for i in range(25):
            create_download_session(
                session, _make_download_session(track_name=f"Track {i}")
            )
        assert len(get_download_sessions(session)) == 20


class TestUpdateDownloadSession:
    def test_update(self, session: Session):
        download = _make_download_session()
        create_download_session(session, download)
        download.status = DownloadSessionStatus.completed
        updated = update_download_session(session, download)
        assert updated.status == DownloadSessionStatus.completed
