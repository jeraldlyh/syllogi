import pytest

from lib.env import (
    get_environment_variable,
    get_environment_variables,
    is_jellyfin_configured,
    is_lastfm_configured,
    is_navidrome_configured,
    is_oauth_configured,
    is_slskd_configured,
)


class TestGetEnvironmentVariable:
    def test_returns_value_when_set(self, monkeypatch):
        monkeypatch.setenv("JELLYFIN_URL", "http://jellyfin.example.com")

        assert get_environment_variable("JELLYFIN_URL") == "http://jellyfin.example.com"

    def test_returns_default_when_not_set(self):
        assert get_environment_variable("NEXT_PUBLIC_URL") == "http://localhost:8000"

    def test_returns_empty_string_for_missing_with_ignore_error(self):
        assert get_environment_variable("REQUIRED_NONEXISTENT") == ""

    def test_returns_empty_string_for_empty_with_ignore_error(self, monkeypatch):
        monkeypatch.setenv("JELLYFIN_URL", "")

        assert get_environment_variable("JELLYFIN_URL") == ""

    def test_raises_when_missing_with_ignore_error_false(self):
        with pytest.raises(ValueError, match="is required but not set"):
            get_environment_variable("REQUIRED_NONEXISTENT", ignore_error=False)

    def test_raises_when_empty_with_ignore_error_false(self, monkeypatch):
        monkeypatch.setenv("JELLYFIN_URL", "")

        with pytest.raises(ValueError, match="is required but not set"):
            get_environment_variable("JELLYFIN_URL", ignore_error=False)

    def test_whitespace_only_counts_as_empty_with_ignore_error_false(self, monkeypatch):
        monkeypatch.setenv("JELLYFIN_URL", "   ")

        with pytest.raises(ValueError, match="is required but not set"):
            get_environment_variable("JELLYFIN_URL", ignore_error=False)


class TestGetEnvironmentVariables:
    def test_returns_defaults_when_unset(self, monkeypatch):
        for var in [
            "JELLYFIN_URL",
            "JELLYFIN_API_KEY",
            "LASTFM_API_KEY",
            "LASTFM_URL",
            "DOWNLOAD_LIBRARY_NAME",
            "DOWNLOAD_DIR",
            "AUTH_SECRET_KEY",
            "NEXT_PUBLIC_URL",
            "DISCORD_WEBHOOK_URL",
            "DATABASE_USERNAME",
            "DATABASE_PASSWORD",
            "DATABASE_URL",
            "DATABASE_NAME",
            "AUTHENTIK_CLIENT_ID",
            "AUTHENTIK_SECRET",
            "AUTHENTIK_ISSUER",
            "ENVIRONMENT",
            "SLSKD_URL",
            "SLSKD_API_KEY",
            "MUSICBRAINZ_URL",
            "MUSICBRAINZ_USER_AGENT",
            "NAVIDROME_URL",
            "NAVIDROME_USERNAME",
            "NAVIDROME_PASSWORD",
            "MUSIC_PROVIDER",
            "LISTENBRAINZ_URL",
            "LISTENBRAINZ_API_KEY",
        ]:
            monkeypatch.delenv(var, raising=False)

        variables = get_environment_variables()

        assert variables["NEXT_PUBLIC_URL"] == "http://localhost:8000"
        assert variables["DOWNLOAD_LIBRARY_NAME"] == "Downloads"
        assert variables["DOWNLOAD_DIR"] == "/downloads"
        assert variables["DATABASE_URL"] == "localhost:5432"
        assert variables["DATABASE_NAME"] == "syllogi"
        assert variables["DISCORD_WEBHOOK_URL"] == ""
        assert variables["IS_DEVELOPMENT"] is False

    def test_reflects_set_environment_variables(self, monkeypatch):
        monkeypatch.setenv("JELLYFIN_URL", "https://jellyfin.example.com")
        monkeypatch.setenv("AUTHENTIK_CLIENT_ID", "test-client-id")

        variables = get_environment_variables()

        assert variables["JELLYFIN_URL"] == "https://jellyfin.example.com"
        assert variables["AUTHENTIK_CLIENT_ID"] == "test-client-id"

    def test_is_development_true_when_environment_is_development(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")

        assert get_environment_variables()["IS_DEVELOPMENT"] is True

    def test_is_development_false_when_other_environment(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")

        assert get_environment_variables()["IS_DEVELOPMENT"] is False

    def test_is_development_false_when_unset(self):
        assert get_environment_variables()["IS_DEVELOPMENT"] is False

    def test_authentik_issuer_strips_trailing_slash(self, monkeypatch):
        monkeypatch.setenv("AUTHENTIK_ISSUER", "https://auth.example.com/")

        assert (
            get_environment_variables()["AUTHENTIK_ISSUER"]
            == "https://auth.example.com"
        )

    def test_authentik_issuer_strips_multiple_trailing_slashes(self, monkeypatch):
        monkeypatch.setenv("AUTHENTIK_ISSUER", "https://auth.example.com///")

        assert (
            get_environment_variables()["AUTHENTIK_ISSUER"]
            == "https://auth.example.com"
        )

    def test_authentik_issuer_preserves_no_slash(self, monkeypatch):
        monkeypatch.setenv("AUTHENTIK_ISSUER", "https://auth.example.com")

        assert (
            get_environment_variables()["AUTHENTIK_ISSUER"]
            == "https://auth.example.com"
        )


class TestIsOauthConfigured:
    def test_returns_true_when_all_vars_set(self, monkeypatch):
        monkeypatch.setenv("AUTHENTIK_CLIENT_ID", "client")
        monkeypatch.setenv("AUTHENTIK_SECRET", "secret")
        monkeypatch.setenv("AUTHENTIK_ISSUER", "https://auth.example.com")

        assert is_oauth_configured() is True

    def test_returns_false_when_client_id_missing(self, monkeypatch):
        monkeypatch.delenv("AUTHENTIK_CLIENT_ID", raising=False)
        monkeypatch.setenv("AUTHENTIK_SECRET", "secret")
        monkeypatch.setenv("AUTHENTIK_ISSUER", "https://auth.example.com")

        assert is_oauth_configured() is False

    def test_returns_false_when_secret_missing(self, monkeypatch):
        monkeypatch.setenv("AUTHENTIK_CLIENT_ID", "client")
        monkeypatch.delenv("AUTHENTIK_SECRET", raising=False)
        monkeypatch.setenv("AUTHENTIK_ISSUER", "https://auth.example.com")

        assert is_oauth_configured() is False

    def test_returns_false_when_issuer_missing(self, monkeypatch):
        monkeypatch.setenv("AUTHENTIK_CLIENT_ID", "client")
        monkeypatch.setenv("AUTHENTIK_SECRET", "secret")
        monkeypatch.delenv("AUTHENTIK_ISSUER", raising=False)

        assert is_oauth_configured() is False


class TestIsSlskdConfigured:
    def test_returns_true_when_all_vars_set(self, monkeypatch):
        monkeypatch.setenv("SLSKD_URL", "https://slskd.example.com")
        monkeypatch.setenv("SLSKD_API_KEY", "api-key")

        assert is_slskd_configured() is True

    def test_returns_false_when_url_missing(self, monkeypatch):
        monkeypatch.delenv("SLSKD_URL", raising=False)
        monkeypatch.setenv("SLSKD_API_KEY", "api-key")

        assert is_slskd_configured() is False

    def test_returns_false_when_api_key_missing(self, monkeypatch):
        monkeypatch.setenv("SLSKD_URL", "https://slskd.example.com")
        monkeypatch.delenv("SLSKD_API_KEY", raising=False)

        assert is_slskd_configured() is False


class TestIsNavidromeConfigured:
    def test_returns_true_when_all_vars_set(self, monkeypatch):
        monkeypatch.setenv("NAVIDROME_URL", "https://navidrome.example.com")
        monkeypatch.setenv("NAVIDROME_USERNAME", "user")
        monkeypatch.setenv("NAVIDROME_PASSWORD", "pass")

        assert is_navidrome_configured() is True

    def test_returns_false_when_url_missing(self, monkeypatch):
        monkeypatch.delenv("NAVIDROME_URL", raising=False)
        monkeypatch.setenv("NAVIDROME_USERNAME", "user")
        monkeypatch.setenv("NAVIDROME_PASSWORD", "pass")

        assert is_navidrome_configured() is False

    def test_returns_false_when_username_missing(self, monkeypatch):
        monkeypatch.setenv("NAVIDROME_URL", "https://navidrome.example.com")
        monkeypatch.delenv("NAVIDROME_USERNAME", raising=False)
        monkeypatch.setenv("NAVIDROME_PASSWORD", "pass")

        assert is_navidrome_configured() is False

    def test_returns_false_when_password_missing(self, monkeypatch):
        monkeypatch.setenv("NAVIDROME_URL", "https://navidrome.example.com")
        monkeypatch.setenv("NAVIDROME_USERNAME", "user")
        monkeypatch.delenv("NAVIDROME_PASSWORD", raising=False)

        assert is_navidrome_configured() is False


class TestIsJellyfinConfigured:
    def test_returns_true_when_all_vars_set(self, monkeypatch):
        monkeypatch.setenv("JELLYFIN_URL", "https://jellyfin.example.com")
        monkeypatch.setenv("JELLYFIN_API_KEY", "api-key")

        assert is_jellyfin_configured() is True

    def test_returns_false_when_url_missing(self, monkeypatch):
        monkeypatch.delenv("JELLYFIN_URL", raising=False)
        monkeypatch.setenv("JELLYFIN_API_KEY", "api-key")

        assert is_jellyfin_configured() is False

    def test_returns_false_when_api_key_missing(self, monkeypatch):
        monkeypatch.setenv("JELLYFIN_URL", "https://jellyfin.example.com")
        monkeypatch.delenv("JELLYFIN_API_KEY", raising=False)

        assert is_jellyfin_configured() is False


class TestIsLastfmConfigured:
    def test_returns_true_when_api_key_set(self, monkeypatch):
        monkeypatch.setenv("LASTFM_API_KEY", "api-key")

        assert is_lastfm_configured() is True

    def test_returns_false_when_api_key_missing(self, monkeypatch):
        monkeypatch.delenv("LASTFM_API_KEY", raising=False)

        assert is_lastfm_configured() is False

