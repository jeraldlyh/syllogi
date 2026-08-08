from unittest.mock import MagicMock, patch

import pytest
from mutagen import MutagenError

from lib.tagger import has_lyrics, is_valid_lyrics


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


class TestHasLyricsFlac:
    @patch("lib.tagger.FLAC")
    def test_returns_true_when_lyrics_tag_present(self, mock_flac):
        mock_audio = MagicMock()
        mock_audio.tags = {"LYRICS": ["test lyrics"]}
        mock_flac.return_value = mock_audio

        assert has_lyrics("test.flac") is True
        mock_flac.assert_called_once_with("test.flac")

    @patch("lib.tagger.FLAC")
    def test_returns_true_when_lyrics_tag_is_lrc_with_text(self, mock_flac):
        mock_audio = MagicMock()
        mock_audio.tags = {"LYRICS": ["[00:12.00]hello world\n[00:15.00]goodbye"]}
        mock_flac.return_value = mock_audio

        assert has_lyrics("test.flac") is True
        mock_flac.assert_called_once_with("test.flac")

    @patch("lib.tagger.FLAC")
    def test_returns_false_when_lyrics_tag_is_empty(self, mock_flac):
        mock_audio = MagicMock()
        mock_audio.tags = {"LYRICS": [""]}
        mock_flac.return_value = mock_audio

        assert has_lyrics("test.flac") is False
        mock_flac.assert_called_once_with("test.flac")

    @patch("lib.tagger.FLAC")
    def test_returns_false_when_lyrics_tag_is_whitespace_only(self, mock_flac):
        mock_audio = MagicMock()
        mock_audio.tags = {"LYRICS": ["\n  \t\n"]}
        mock_flac.return_value = mock_audio

        assert has_lyrics("test.flac") is False
        mock_flac.assert_called_once_with("test.flac")

    @patch("lib.tagger.FLAC")
    def test_returns_false_when_lyrics_tag_is_timestamp_only(self, mock_flac):
        mock_audio = MagicMock()
        mock_audio.tags = {"LYRICS": ["[00:00.00]\n[00:05.00]"]}
        mock_flac.return_value = mock_audio

        assert has_lyrics("test.flac") is False
        mock_flac.assert_called_once_with("test.flac")

    @patch("lib.tagger.FLAC")
    def test_returns_false_when_no_lyrics_tag(self, mock_flac):
        mock_audio = MagicMock()
        mock_audio.tags = {}
        mock_flac.return_value = mock_audio

        assert has_lyrics("test.flac") is False
        mock_flac.assert_called_once_with("test.flac")

    @patch("lib.tagger.FLAC")
    def test_returns_false_when_no_tags(self, mock_flac):
        mock_audio = MagicMock()
        mock_audio.tags = None
        mock_flac.return_value = mock_audio

        assert has_lyrics("test.flac") is False
        mock_flac.assert_called_once_with("test.flac")

    @patch("lib.tagger.FLAC")
    def test_returns_false_on_mutagen_error(self, mock_flac):
        mock_flac.side_effect = MutagenError("boom")

        assert has_lyrics("test.flac") is False
        mock_flac.assert_called_once_with("test.flac")


class TestHasLyricsMp3:
    @patch("lib.tagger.MP3")
    def test_returns_true_when_uslt_tag_present(self, mock_mp3):
        mock_audio = MagicMock()
        mock_tag = MagicMock()
        mock_tag.text = "test lyrics"
        mock_audio.tags.getall.return_value = [mock_tag]
        mock_mp3.return_value = mock_audio

        assert has_lyrics("test.mp3") is True
        mock_mp3.assert_called_once_with("test.mp3")

    @patch("lib.tagger.MP3")
    def test_returns_false_when_uslt_text_empty(self, mock_mp3):
        mock_audio = MagicMock()
        mock_tag = MagicMock()
        mock_tag.text = "   "
        mock_audio.tags.getall.return_value = [mock_tag]
        mock_mp3.return_value = mock_audio

        assert has_lyrics("test.mp3") is False
        mock_mp3.assert_called_once_with("test.mp3")

    @patch("lib.tagger.MP3")
    def test_returns_false_when_uslt_timestamp_only(self, mock_mp3):
        mock_audio = MagicMock()
        mock_tag = MagicMock()
        mock_tag.text = "[00:00.00]\n[00:05.00]"
        mock_audio.tags.getall.return_value = [mock_tag]
        mock_mp3.return_value = mock_audio

        assert has_lyrics("test.mp3") is False
        mock_mp3.assert_called_once_with("test.mp3")

    @patch("lib.tagger.MP3")
    def test_returns_false_when_no_uslt_tag(self, mock_mp3):
        mock_audio = MagicMock()
        mock_audio.tags.getall.return_value = []
        mock_mp3.return_value = mock_audio

        assert has_lyrics("test.mp3") is False
        mock_mp3.assert_called_once_with("test.mp3")

    @patch("lib.tagger.MP3")
    def test_returns_false_when_no_tags(self, mock_mp3):
        mock_audio = MagicMock()
        mock_audio.tags = None
        mock_mp3.return_value = mock_audio

        assert has_lyrics("test.mp3") is False
        mock_mp3.assert_called_once_with("test.mp3")

    @patch("lib.tagger.MP3")
    def test_returns_false_on_mutagen_error(self, mock_mp3):
        mock_mp3.side_effect = MutagenError("boom")

        assert has_lyrics("test.mp3") is False
        mock_mp3.assert_called_once_with("test.mp3")


class TestHasLyricsOpus:
    @patch("lib.tagger.OggOpus")
    def test_returns_true_when_lyrics_tag_present(self, mock_ogg_opus):
        mock_audio = MagicMock()
        mock_audio.tags = {"LYRICS": ["test lyrics"]}
        mock_ogg_opus.return_value = mock_audio

        assert has_lyrics("test.opus") is True
        mock_ogg_opus.assert_called_once_with("test.opus")

    @patch("lib.tagger.OggOpus")
    def test_returns_false_when_no_lyrics_tag(self, mock_ogg_opus):
        mock_audio = MagicMock()
        mock_audio.tags = {}
        mock_ogg_opus.return_value = mock_audio

        assert has_lyrics("test.opus") is False
        mock_ogg_opus.assert_called_once_with("test.opus")


class TestHasLyricsUnsupported:
    def test_returns_false_for_unsupported_extension(self):
        assert has_lyrics("test.wav") is False

    def test_returns_false_for_nonexistent_file(self):
        assert has_lyrics("missing.ogg") is False
