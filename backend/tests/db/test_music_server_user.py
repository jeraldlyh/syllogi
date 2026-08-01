import uuid

from sqlmodel import Session

from db.models.music_server_user import MusicServerProvider, MusicServerUser
from db.music_server_user import (
    create_music_server_user,
    delete_music_server_user,
    get_music_server_user_by_id,
    get_music_server_user_by_username,
    get_music_server_users,
    get_music_server_users_by_provider,
    update_music_server_user,
)


def _make_music_server_user(**overrides) -> MusicServerUser:
    defaults = {
        "username": "testuser",
        "provider": MusicServerProvider.jellyfin,
        "password": "",
        "lastfm_username": "",
        "listenbrainz_username": "",
    }
    defaults.update(overrides)
    return MusicServerUser(**defaults)


class TestCreateMusicServerUser:
    def test_create(self, session: Session):
        user = _make_music_server_user()
        create_music_server_user(session, user)

        assert user.id is not None


class TestGetMusicServerUsers:
    def test_empty(self, session: Session):
        assert get_music_server_users(session) == []

    def test_multiple(self, session: Session):
        create_music_server_user(session, _make_music_server_user(username="u1"))
        create_music_server_user(session, _make_music_server_user(username="u2"))

        assert len(get_music_server_users(session)) == 2


class TestGetMusicServerUserById:
    def test_found(self, session: Session):
        user = _make_music_server_user()
        create_music_server_user(session, user)

        assert get_music_server_user_by_id(session, user.id) is not None

    def test_not_found(self, session: Session):
        assert get_music_server_user_by_id(session, uuid.uuid4()) is None


class TestGetMusicServerUserByUsername:
    def test_found(self, session: Session):
        create_music_server_user(session, _make_music_server_user(username="alice"))
        result = get_music_server_user_by_username(
            session, "alice", MusicServerProvider.jellyfin
        )

        assert result is not None

    def test_wrong_provider(self, session: Session):
        create_music_server_user(session, _make_music_server_user(username="alice"))
        result = get_music_server_user_by_username(
            session, "alice", MusicServerProvider.navidrome
        )

        assert result is None

    def test_not_found(self, session: Session):
        assert (
            get_music_server_user_by_username(
                session, "nobody", MusicServerProvider.jellyfin
            )
            is None
        )


class TestGetMusicServerUsersByProvider:
    def test_filters_by_provider(self, session: Session):
        create_music_server_user(
            session,
            _make_music_server_user(
                username="u1", provider=MusicServerProvider.jellyfin
            ),
        )
        create_music_server_user(
            session,
            _make_music_server_user(
                username="u2", provider=MusicServerProvider.navidrome
            ),
        )
        jellyfin_users = get_music_server_users_by_provider(
            session, MusicServerProvider.jellyfin
        )

        assert len(jellyfin_users) == 1
        assert jellyfin_users[0].username == "u1"


class TestUpdateMusicServerUser:
    def test_update(self, session: Session):
        user = _make_music_server_user()
        create_music_server_user(session, user)

        user.lastfm_username = "lastfm_user"
        update_music_server_user(session, user)

        result = get_music_server_user_by_id(session, user.id)

        assert result is not None
        assert result.lastfm_username == "lastfm_user"


class TestDeleteMusicServerUser:
    def test_delete(self, session: Session):
        user = _make_music_server_user()
        create_music_server_user(session, user)
        delete_music_server_user(session, user)
        assert get_music_server_user_by_id(session, user.id) is None
