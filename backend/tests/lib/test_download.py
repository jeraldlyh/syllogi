from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from lib.download import download_missing_tracks, upgrade_non_lossless_tracks
from lib.models.common import ExternalTrack
from lib.models.provider import ProviderTrack


def _make_external_track(
    artist_name="Test Artist",
    track_name="Test Track",
    album_name="Test Album",
    year="2024",
    duration=300,
) -> ExternalTrack:
    return ExternalTrack(
        artist_name=artist_name,
        track_name=track_name,
        album_name=album_name,
        year=year,
        duration=duration,
    )


def _make_provider_track(
    track_name="Test Track",
    album_name="Test Album",
    artists=None,
    duration_ticks=3000000000,  # NOTE: 300 seconds
) -> ProviderTrack:
    return ProviderTrack(
        id="track-1",
        track_name=track_name,
        album_name=album_name,
        album_id="",
        musicbrainz_id="",
        artists=artists or ["Test Artist"],
        duration_ticks=duration_ticks,
        year="2024",
    )


@contextmanager
def _patch_download_mocks(**overrides):
    defaults = {
        "is_track_exists_in_path": MagicMock(return_value=False),
        "is_slskd_configured": MagicMock(return_value=True),
        "download_track_slskd": AsyncMock(return_value=True),
        "download_track_youtube": AsyncMock(return_value=False),
        "get_existing_track_path": MagicMock(return_value=None),
        "tag_audio_file": AsyncMock(),
        "MusicBrainzMetadataProvider": MagicMock(),
    }
    defaults.update(overrides)

    mocks = {}

    for name, mock in defaults.items():
        patcher = patch(f"lib.download.{name}", mock)
        patcher.start()
        mocks[name] = mock

    try:
        yield mocks
    finally:
        patch.stopall()


@contextmanager
def _patch_upgrade_mocks(**overrides):
    defaults = {
        "is_slskd_configured": MagicMock(return_value=True),
        "is_track_exists_in_path": MagicMock(return_value=True),
        "is_track_lossless": MagicMock(return_value=False),
        "get_existing_track_path": MagicMock(return_value="/music/Test Track.mp3"),
        "os.remove": MagicMock(),
        "download_track_slskd": AsyncMock(return_value=True),
    }
    defaults.update(overrides)

    mocks = {}

    for name, mock in defaults.items():
        patcher = patch(f"lib.download.{name}", mock)
        patcher.start()
        mocks[name] = mock

    try:
        yield mocks
    finally:
        patch.stopall()


class TestDownloadMissingTracks:
    async def test_returns_found_when_track_already_exists(self):
        song = _make_external_track()

        with _patch_download_mocks(
            is_track_exists_in_path=MagicMock(return_value=True)
        ) as mocks:
            found, missing = await download_missing_tracks(missing_tracks=[song])

        assert found == [song]
        assert missing == []
        mocks["download_track_slskd"].assert_not_awaited()
        mocks["download_track_youtube"].assert_not_awaited()

    async def test_downloads_via_slskd_when_enabled(self):
        song = _make_external_track()
        existing_path = "/music/Test Artist/Test Album/Test Track.mp3"

        mb_track = MagicMock()
        mb_track.track_name = "MB Track"
        mb_track.album_name = "MB Album"
        mb_track.genres = ["Rock"]

        mb_provider_instance = MagicMock()
        mb_provider_instance.get_artist_track = AsyncMock(return_value=mb_track)
        mb_provider_class = MagicMock(return_value=mb_provider_instance)

        with _patch_download_mocks(
            get_existing_track_path=MagicMock(return_value=existing_path),
            MusicBrainzMetadataProvider=mb_provider_class,
        ) as mocks:
            found, missing = await download_missing_tracks(missing_tracks=[song])

        assert found == [song]
        assert missing == []
        mocks["download_track_slskd"].assert_awaited_once_with(
            artist_name="Test Artist",
            track_name="Test Track",
            album_name="Test Album",
            duration=300,
        )
        mocks["download_track_youtube"].assert_not_awaited()
        mocks["tag_audio_file"].assert_awaited_once_with(
            file_path=existing_path,
            artist_name="Test Artist",
            track_name="MB Track",
            album_name="MB Album",
            year="2024",
            genres=["Rock"],
            duration=300,
        )

    async def test_falls_back_to_youtube_when_slskd_fails(self):
        song = _make_external_track()

        with _patch_download_mocks(
            download_track_slskd=AsyncMock(return_value=False),
            download_track_youtube=AsyncMock(return_value=True),
        ) as mocks:
            found, missing = await download_missing_tracks(missing_tracks=[song])

        assert found == [song]
        assert missing == []
        mocks["download_track_slskd"].assert_awaited_once()
        mocks["download_track_youtube"].assert_awaited_once_with(
            artist_name="Test Artist",
            track_name="Test Track",
            album_name="Test Album",
        )
        mocks["tag_audio_file"].assert_not_awaited()

    async def test_returns_missing_when_all_downloads_fail(self):
        song = _make_external_track()

        with _patch_download_mocks(
            download_track_slskd=AsyncMock(return_value=False),
            download_track_youtube=AsyncMock(return_value=False),
        ) as mocks:
            found, missing = await download_missing_tracks(missing_tracks=[song])

        assert found == []
        assert missing == [song]
        mocks["download_track_slskd"].assert_awaited_once()
        mocks["download_track_youtube"].assert_awaited_once()

    async def test_handles_multiple_tracks(self):
        existing_song = _make_external_track(track_name="Existing Track")
        downloaded_song = _make_external_track(track_name="Downloaded Track")
        still_missing_song = _make_external_track(track_name="Still Missing Track")

        def exists_side_effect(artist_name, track_name, album_name):
            return track_name == "Existing Track"

        def slskd_side_effect(artist_name, track_name, album_name, duration):
            return track_name == "Downloaded Track"

        with _patch_download_mocks(
            is_track_exists_in_path=MagicMock(side_effect=exists_side_effect),
            download_track_slskd=AsyncMock(side_effect=slskd_side_effect),
            download_track_youtube=AsyncMock(return_value=False),
        ) as mocks:
            found, missing = await download_missing_tracks(
                missing_tracks=[existing_song, downloaded_song, still_missing_song]
            )

        assert found == [existing_song, downloaded_song]
        assert missing == [still_missing_song]
        mocks["download_track_slskd"].assert_awaited()
        mocks["download_track_youtube"].assert_awaited_once()


class TestUpgradeNonLosslessTracks:
    async def test_returns_empty_when_slskd_not_configured(self):
        track = _make_provider_track()

        with _patch_upgrade_mocks(
            is_slskd_configured=MagicMock(return_value=False)
        ) as mocks:
            upgraded = await upgrade_non_lossless_tracks(tracks=[track])

        assert upgraded == []
        mocks["download_track_slskd"].assert_not_awaited()
        mocks["os.remove"].assert_not_called()

    async def test_skips_track_not_on_disk(self):
        track = _make_provider_track()

        with _patch_upgrade_mocks(
            is_track_exists_in_path=MagicMock(return_value=False)
        ) as mocks:
            upgraded = await upgrade_non_lossless_tracks(tracks=[track])

        assert upgraded == []
        mocks["download_track_slskd"].assert_not_awaited()
        mocks["os.remove"].assert_not_called()

    async def test_skips_already_lossless_track(self):
        track = _make_provider_track()

        with _patch_upgrade_mocks(
            is_track_lossless=MagicMock(return_value=True)
        ) as mocks:
            upgraded = await upgrade_non_lossless_tracks(tracks=[track])

        assert upgraded == []
        mocks["download_track_slskd"].assert_not_awaited()
        mocks["os.remove"].assert_not_called()

    async def test_skips_track_without_existing_path(self):
        track = _make_provider_track()

        with _patch_upgrade_mocks(
            get_existing_track_path=MagicMock(return_value=None)
        ) as mocks:
            upgraded = await upgrade_non_lossless_tracks(tracks=[track])

        assert upgraded == []
        mocks["download_track_slskd"].assert_not_awaited()
        mocks["os.remove"].assert_not_called()

    async def test_upgrades_non_lossless_track(self):
        track = _make_provider_track()

        with _patch_upgrade_mocks() as mocks:
            upgraded = await upgrade_non_lossless_tracks(tracks=[track])

        assert upgraded == [track]
        mocks["os.remove"].assert_called_once_with("/music/Test Track.mp3")
        mocks["download_track_slskd"].assert_awaited_once_with(
            artist_name="Test Artist",
            track_name="Test Track",
            album_name="Test Album",
            duration=300,
            lossless_only=True,
        )

    async def test_returns_empty_when_slskd_download_fails(self):
        track = _make_provider_track()

        with _patch_upgrade_mocks(
            download_track_slskd=AsyncMock(return_value=False)
        ) as mocks:
            upgraded = await upgrade_non_lossless_tracks(tracks=[track])

        assert upgraded == []
        mocks["os.remove"].assert_called_once()
        mocks["download_track_slskd"].assert_awaited_once_with(
            artist_name="Test Artist",
            track_name="Test Track",
            album_name="Test Album",
            duration=300,
            lossless_only=True,
        )
