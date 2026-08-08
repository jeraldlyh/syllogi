import uuid

from sqlmodel import Session

from db.models.sync import Sync, SyncProvider
from db.sync import (
    create_sync,
    delete_sync,
    get_sync_by_id,
    get_syncs,
    update_sync,
)


def _make_sync(**overrides) -> Sync:
    defaults = {
        "provider": SyncProvider.spotify,
        "playlist_id": "playlist-123",
        "playlist_name": "My Playlist",
        "username": "testuser",
        "enable_sync": True,
        "enable_download": True,
        "is_public": False,
        "cron_expression": "",
    }
    defaults.update(overrides)
    return Sync(**defaults)


class TestCreateSync:
    def test_create(self, session: Session):
        sync = _make_sync()
        create_sync(session, sync)

        assert sync.id is not None


class TestGetSyncs:
    def test_empty(self, session: Session):
        assert get_syncs(session) == []

    def test_multiple(self, session: Session):
        create_sync(session, _make_sync(playlist_id="p1"))
        create_sync(session, _make_sync(playlist_id="p2"))

        assert len(get_syncs(session)) == 2


class TestGetSyncById:
    def test_found(self, session: Session):
        sync = _make_sync()
        create_sync(session, sync)

        assert get_sync_by_id(session, sync.id) is not None

    def test_not_found(self, session: Session):
        assert get_sync_by_id(session, uuid.uuid4()) is None


class TestUpdateSync:
    def test_update(self, session: Session):
        sync = _make_sync()
        create_sync(session, sync)

        sync.playlist_name = "Updated Name"
        update_sync(session, sync)

        result = get_sync_by_id(session, sync.id)

        assert result is not None
        assert result.playlist_name == "Updated Name"


class TestDeleteSync:
    def test_delete(self, session: Session):
        sync = _make_sync()
        create_sync(session, sync)
        delete_sync(session, sync)

        assert get_sync_by_id(session, sync.id) is None
