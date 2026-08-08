import pytest


@pytest.fixture(autouse=True)
def _provider_env(monkeypatch):
    monkeypatch.setenv("JELLYFIN_API_KEY", "test-jellyfin-api-key")
    monkeypatch.setenv("JELLYFIN_URL", "https://jellyfin.example.com")
    monkeypatch.setenv("DOWNLOAD_LIBRARY_NAME", "Downloads")
    monkeypatch.setenv("DOWNLOAD_DIR", "/mnt/music/downloads")
    monkeypatch.setenv("NAVIDROME_URL", "https://navidrome.example.com")
    monkeypatch.setenv("NAVIDROME_USERNAME", "admin")
    monkeypatch.setenv("NAVIDROME_PASSWORD", "adminpass")
