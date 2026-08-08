import uuid

from sqlmodel import Session

from db.models.user import User
from db.user import (
    count_users,
    create_user,
    delete_user,
    get_user_by_id,
    get_user_by_oauth_id,
    get_user_by_username,
    get_users,
    update_user,
)


def _make_user(**overrides) -> User:
    defaults = {
        "username": "testuser",
        "password": "hashed_password",
        "oauth_id": None,
        "is_admin": False,
    }
    defaults.update(overrides)
    return User(**defaults)


class TestCreateUser:
    def test_create_user(self, session: Session):
        user = _make_user()
        create_user(session, user)

        assert user.id is not None

    def test_create_user_with_oauth(self, session: Session):
        oauth_id = "oauth-123"
        user = _make_user(oauth_id=oauth_id)
        create_user(session, user)

        result = get_user_by_oauth_id(session, oauth_id)

        assert result is not None
        assert result.id == user.id


class TestGetUsers:
    def test_get_users_empty(self, session: Session):
        assert get_users(session) == []

    def test_get_users_multiple(self, session: Session):
        create_user(session, _make_user(username="user1"))
        create_user(session, _make_user(username="user2"))

        users = get_users(session)
        assert len(users) == 2


class TestGetUserById:
    def test_get_user_by_id_found(self, session: Session):
        user = _make_user()
        create_user(session, user)

        result = get_user_by_id(session, user.id)

        assert result is not None
        assert result.username == "testuser"

    def test_get_user_by_id_not_found(self, session: Session):
        assert get_user_by_id(session, uuid.uuid4()) is None


class TestGetUserByUsername:
    def test_get_user_by_username_found(self, session: Session):
        username = "alice"
        create_user(session, _make_user(username=username))

        result = get_user_by_username(session, username)

        assert result is not None
        assert result.username == username

    def test_get_user_by_username_not_found(self, session: Session):
        assert get_user_by_username(session, "nobody") is None


class TestGetUserByOauthId:
    def test_get_user_by_oauth_id_found(self, session: Session):
        oauth_id = "oauth-abc"
        create_user(session, _make_user(oauth_id=oauth_id))

        result = get_user_by_oauth_id(session, oauth_id)

        assert result is not None

    def test_get_user_by_oauth_id_not_found(self, session: Session):
        assert get_user_by_oauth_id(session, "nonexistent") is None


class TestCountUsers:
    def test_count_users_empty(self, session: Session):
        assert count_users(session) == 0

    def test_count_users(self, session: Session):
        create_user(session, _make_user(username="u1"))
        create_user(session, _make_user(username="u2"))
        create_user(session, _make_user(username="u3"))

        assert count_users(session) == 3


class TestUpdateUser:
    def test_update_user(self, session: Session):
        user = _make_user()
        create_user(session, user)

        user.username = "updated"
        update_user(session, user)

        result = get_user_by_id(session, user.id)

        assert result is not None
        assert result.username == "updated"


class TestDeleteUser:
    def test_delete_user(self, session: Session):
        user = _make_user()
        create_user(session, user)
        delete_user(session, user)

        assert get_user_by_id(session, user.id) is None

    def test_delete_user_count(self, session: Session):
        user = _make_user()
        create_user(session, user)
        delete_user(session, user)

        assert count_users(session) == 0
