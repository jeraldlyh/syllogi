from unittest.mock import AsyncMock, patch

import pytest

from lib.models.library import AudioTags, LyricsCandidate
from lib.tagger import get_tag_frames, is_valid_lyrics, tag_audio_file


def make_candidate(**overrides) -> LyricsCandidate:
    fields = {
        "id": 1,
        "track_name": "Blinding Lights",
        "artist_name": "The Weeknd",
        "album_name": "After Hours",
        "duration": 200,
        "instrumental": False,
        "plain_lyrics": "I've been tryna call",
        "synced_lyrics": "[00:03.45] I've been tryna call",
    }
    fields.update(overrides)

    return LyricsCandidate(**fields)


class TestIsValidLyrics:
    @pytest.mark.parametrize(
        "text",
        [
            None,
            "",
            "   ",
            "\n\t\n",
            "[00:00.00]\n[00:05.00]",
            "[00:00.00][00:05.00]",
            "[00:00.00]\n\n[00:05.00]\n  ",
        ],
    )
    def test_rejects_invalid_content(self, text):
        assert is_valid_lyrics(text) is False

    @pytest.mark.parametrize(
        "text",
        [
            "test lyrics",
            "hello world\nsecond line",
            "[00:12.00]hello world\n[00:15.00]goodbye",
            "[00:12.00][00:15.00]hello world",
            "  \nlyrics\n",
        ],
    )
    def test_accepts_meaningful_content(self, text):
        assert is_valid_lyrics(text) is True


class TestGetTagFrames:
    def test_reports_id3_frames_for_mp3(self):
        frames = get_tag_frames("Artist/Track.mp3")

        assert frames["title"] == "TIT2"
        assert frames["musicbrainz_id"] == "UFID"

    @pytest.mark.parametrize("file_path", ["Artist/Track.flac", "Artist/Track.opus"])
    def test_reports_vorbis_frames_for_flac_and_opus(self, file_path):
        frames = get_tag_frames(file_path)

        assert frames["title"] == "TITLE"
        assert frames["musicbrainz_id"] == "MUSICBRAINZ_TRACKID"


class TestTagAudioFile:
    @staticmethod
    def _patch(existing: AudioTags, candidates: list[LyricsCandidate] | None = None):
        return (
            patch("lib.tagger.read_audio_tags", return_value=(existing, 200)),
            patch("lib.tagger.write_audio_tags"),
            patch(
                "lib.tagger.LRCLIBLyricsProvider.search_lyrics",
                new=AsyncMock(return_value=candidates or []),
            ),
        )

    async def test_writes_the_supplied_metadata(self):
        existing = AudioTags()
        read, write, search = self._patch(existing)

        with read, write as mock_write, search:
            result = await tag_audio_file(
                file_path="Track.flac",
                artist_name="The Weeknd",
                track_name="Blinding Lights",
                album_name="After Hours",
                year="2020",
                genres=["synth-pop"],
                duration=200,
            )

        assert result is True
        written = mock_write.call_args.kwargs["tags"]
        assert written.title == "Blinding Lights"
        assert written.artist == "The Weeknd"
        assert written.album == "After Hours"
        assert written.date == "2020"
        assert written.genres == ["synth-pop"]

    async def test_keeps_lyrics_already_on_the_file(self):
        existing = AudioTags(lyrics="[00:03.45] I've been tryna call")
        read, write, search = self._patch(existing)

        with read, write as mock_write, search as mock_search:
            await tag_audio_file(
                file_path="Track.flac",
                artist_name="The Weeknd",
                track_name="Blinding Lights",
                album_name="After Hours",
                year="2020",
                genres=[],
                duration=200,
            )

        assert mock_write.call_args.kwargs["tags"].lyrics == existing.lyrics
        mock_search.assert_not_awaited()

    async def test_keeps_the_musicbrainz_id_already_on_the_file(self):
        existing = AudioTags(musicbrainz_id="9b1a2b3c")
        read, write, search = self._patch(existing)

        with read, write as mock_write, search:
            await tag_audio_file(
                file_path="Track.flac",
                artist_name="The Weeknd",
                track_name="Blinding Lights",
                album_name="",
                year="",
                genres=[],
                duration=200,
            )

        assert mock_write.call_args.kwargs["tags"].musicbrainz_id == "9b1a2b3c"

    async def test_keeps_existing_values_when_no_replacement_is_supplied(self):
        existing = AudioTags(album="After Hours", date="2020", genres=["synth-pop"])
        read, write, search = self._patch(existing)

        with read, write as mock_write, search:
            await tag_audio_file(
                file_path="Track.flac",
                artist_name="The Weeknd",
                track_name="Blinding Lights",
                album_name="",
                year="",
                genres=[],
                duration=200,
            )

        written = mock_write.call_args.kwargs["tags"]
        assert written.album == "After Hours"
        assert written.date == "2020"
        assert written.genres == ["synth-pop"]

    async def test_fetches_lyrics_when_the_file_has_none(self):
        existing = AudioTags()
        read, write, search = self._patch(existing, [make_candidate()])

        with read, write as mock_write, search as mock_search:
            await tag_audio_file(
                file_path="Track.flac",
                artist_name="The Weeknd",
                track_name="Blinding Lights",
                album_name="After Hours",
                year="2020",
                genres=[],
                duration=200,
            )

        mock_search.assert_awaited_once()
        assert (
            mock_write.call_args.kwargs["tags"].lyrics
            == "[00:03.45] I've been tryna call"
        )

    async def test_leaves_lyrics_empty_when_no_candidate_matches(self):
        existing = AudioTags()
        read, write, search = self._patch(existing, [make_candidate(duration=400)])

        with read, write as mock_write, search:
            await tag_audio_file(
                file_path="Track.flac",
                artist_name="The Weeknd",
                track_name="Blinding Lights",
                album_name="After Hours",
                year="2020",
                genres=[],
                duration=200,
            )

        assert mock_write.call_args.kwargs["tags"].lyrics == ""

    async def test_returns_false_for_an_unreadable_file(self):
        with patch("lib.tagger.read_audio_tags", return_value=None):
            result = await tag_audio_file(
                file_path="Track.wav",
                artist_name="The Weeknd",
                track_name="Blinding Lights",
                album_name="After Hours",
                year="2020",
                genres=[],
            )

        assert result is False

    async def test_returns_false_when_the_write_fails(self):
        existing = AudioTags()
        read, _, search = self._patch(existing)

        with (
            read,
            patch("lib.tagger.write_audio_tags", side_effect=OSError("disk full")),
            search,
        ):
            result = await tag_audio_file(
                file_path="Track.flac",
                artist_name="The Weeknd",
                track_name="Blinding Lights",
                album_name="After Hours",
                year="2020",
                genres=[],
            )

        assert result is False
