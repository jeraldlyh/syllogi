from datetime import UTC, datetime, timedelta

import jwt

from lib.auth import (
    ALGORITHM,
    AUTH_SECRET_KEY,
    _get_password_hash,
    _verify_password,
    create_access_token,
)


class TestPasswordHashing:
    def test_hash_returns_nonempty_string(self):
        hashed = _get_password_hash("secret")

        assert isinstance(hashed, str)
        assert hashed != ""

    def test_verify_correct_password(self):
        hashed = _get_password_hash("secret")

        assert _verify_password("secret", hashed) is True

    def test_verify_wrong_password(self):
        hashed = _get_password_hash("secret")

        assert _verify_password("wrong", hashed) is False

    def test_different_hashes_for_same_input(self):
        a = _get_password_hash("secret")
        b = _get_password_hash("secret")

        assert a != b

    def test_verify_empty_password(self):
        hashed = _get_password_hash("")

        assert _verify_password("", hashed) is True


class TestCreateAccessToken:
    def test_creates_valid_jwt(self):
        token = create_access_token({"sub": "alice"})
        payload = jwt.decode(
            token, AUTH_SECRET_KEY, algorithms=[ALGORITHM]
        )

        assert payload["sub"] == "alice"

    def test_token_contains_expiry(self):
        token = create_access_token({"sub": "alice"})
        payload = jwt.decode(
            token, AUTH_SECRET_KEY, algorithms=[ALGORITHM]
        )

        assert "exp" in payload

    def test_custom_expires_delta(self):
        before = datetime.now(UTC)
        token = create_access_token(
            {"sub": "alice"}, expires_delta=timedelta(minutes=60)
        )
        payload = jwt.decode(
            token, AUTH_SECRET_KEY, algorithms=[ALGORITHM]
        )

        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        delta = exp - before.replace(tzinfo=UTC)

        assert abs(delta.total_seconds() - 3600) < 5

    def test_default_expires_delta(self):
        before = datetime.now(UTC)
        token = create_access_token({"sub": "alice"})
        payload = jwt.decode(
            token, AUTH_SECRET_KEY, algorithms=[ALGORITHM]
        )

        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        delta = exp - before.replace(tzinfo=UTC)

        assert abs(delta.total_seconds() - 1800) < 5

