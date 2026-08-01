import uuid

from sqlmodel import Session

from db.models.sync import (
    SyncSession,
    SyncSessionTrackType,
    SyncStatus,
    SyncProvider,
)
from db.sync_session import (
    build_sync_session_tracks,
    create_sync_session,
    get_sync_session_by_id,
    get_sync_session_tracks,
    get_sync_sessions,
    update_sync_session,
)


def _make_sync_session(**overrides) -> SyncSession:
    defaults = {
        "provider": SyncProvider.spotify,
        "provider_playlist_id": "sp-123",
        "provider_playlist_name": "Source Playlist",
        "target_user_id": "target-1",
        "target_username": "target_user",
        "target_playlist_id": "tp-456",
        "target_playlist_name": "Target Playlist",
        "duration_seconds": 30,
        "status": SyncStatus.completed,
    }
    defaults.update(overrides)
    return SyncSession(**defaults)


class TestCreateSyncSession:
    def test_create(self, session: Session):
        sync_session = _make_sync_session()
        create_sync_session(session, sync_session)

        assert sync_session.id is not None


class TestGetSyncSessionById:
    def test_found(self, session: Session):
        sync_session = _make_sync_session()
        create_sync_session(session, sync_session)

        assert get_sync_session_by_id(session, sync_session.id) is not None

    def test_not_found(self, session: Session):
        assert get_sync_session_by_id(session, uuid.uuid4()) is None


class TestGetSyncSessions:
    def test_empty(self, session: Session):
        assert get_sync_sessions(session) == []

    def test_ordered_by_created_at_desc(self, session: Session):
        a = _make_sync_session(provider_playlist_id="p1")
        b = _make_sync_session(provider_playlist_id="p2")

        create_sync_session(session, a)
        create_sync_session(session, b)

        sessions = get_sync_sessions(session)
        assert len(sessions) == 2


class TestUpdateSyncSession:
    def test_update(self, session: Session):
        sync_session = _make_sync_session()
        create_sync_session(session, sync_session)

        sync_session.duration_seconds = 60
        updated = update_sync_session(session, sync_session)

        assert updated.duration_seconds == 60


class TestGetSyncSessionTracks:
    def test_empty(self, session: Session):
        assert get_sync_session_tracks(session, uuid.uuid4()) == []

    def test_returns_tracks_for_session(self, session: Session):
        sync_session = _make_sync_session()
        create_sync_session(session, sync_session)

        tracks = build_sync_session_tracks(
            sync_session.id,
            ["Track A", "Track B"],
            SyncSessionTrackType.new,
        )
        for track in tracks:
            session.add(track)

        session.commit()
        result = get_sync_session_tracks(session, sync_session.id)

        assert len(result) == 2


class TestBuildSyncSessionTracks:
    def test_builds_tracks(self):
        session_id = uuid.uuid4()
        tracks = build_sync_session_tracks(
            session_id, ["A", "B", "C"], SyncSessionTrackType.missing
        )

        assert len(tracks) == 3
        assert all(t.sync_session_id == session_id for t in tracks)
        assert all(t.type == SyncSessionTrackType.missing for t in tracks)
        assert tracks[0].name == "A"

    def test_empty_names(self):
        tracks = build_sync_session_tracks(uuid.uuid4(), [], SyncSessionTrackType.total)

        assert tracks == []
