import httpx
import pytest
import respx
from fastapi import HTTPException

from lib.authentik import (
    _get_authentik_config,
    get_authentik_token,
    get_authentik_userinfo,
)

TOKEN_URL = "https://auth.example.com/application/o/token/"
USERINFO_URL = "https://auth.example.com/application/o/userinfo/"
OAUTH_URL = "http://localhost"
OAUTH_CODE = "code-abc"


@pytest.fixture(autouse=True)
def _authentik_env(monkeypatch):
    monkeypatch.setenv("AUTHENTIK_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("AUTHENTIK_SECRET", "test-secret")
    monkeypatch.setenv(
        "AUTHENTIK_ISSUER", "https://auth.example.com/application/o/syllogi/"
    )


class TestGetAuthentikConfig:
    def test_returns_correct_config(self):
        config = _get_authentik_config()

        assert config["client_id"] == "test-client-id"
        assert config["client_secret"] == "test-secret"
        assert config["issuer"] == "https://auth.example.com/application/o/syllogi"

    def test_strips_issuer_trailing_slash(self):
        config = _get_authentik_config()

        assert not config["issuer"].endswith("/")

    def test_builds_correct_urls(self):
        config = _get_authentik_config()

        assert config["authorize_url"] == (
            "https://auth.example.com/application/o/authorize/"
        )
        assert config["token_url"] == TOKEN_URL
        assert config["userinfo_url"] == USERINFO_URL


class TestGetAuthToken:
    @respx.mock
    async def test_returns_access_token_on_success(self):
        respx.post(TOKEN_URL).mock(
            return_value=httpx.Response(200, json={"access_token": "token-123"})
        )

        result = await get_authentik_token(oauth_url=OAUTH_URL, oauth_code=OAUTH_CODE)

        assert result == "token-123"

    @respx.mock
    async def test_raises_on_failure(self):
        respx.post(TOKEN_URL).mock(return_value=httpx.Response(401))

        with pytest.raises(HTTPException):
            await get_authentik_token(oauth_url=OAUTH_URL, oauth_code=OAUTH_CODE)


class TestGetAuthentikUserinfo:
    @respx.mock
    async def test_returns_userinfo_on_success(self):
        respx.get(USERINFO_URL).mock(
            return_value=httpx.Response(
                200,
                json={"preferred_username": "alice", "email": "alice@example.com"},
            )
        )

        result = await get_authentik_userinfo(access_token="token-123")

        assert result["preferred_username"] == "alice"
        assert result["email"] == "alice@example.com"

    @respx.mock
    async def test_raises_on_failure(self):
        respx.get(USERINFO_URL).mock(return_value=httpx.Response(401))

        with pytest.raises(HTTPException):
            await get_authentik_userinfo(access_token="token-123")
