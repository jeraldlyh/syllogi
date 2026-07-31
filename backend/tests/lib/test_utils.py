import pytest

from lib.utils import (
    get_clean_name,
    convert_seconds_to_readable_time,
    parse_cron_expression,
    sanitize_filename,
    normalize,
    truncate,
)


class TestGetCleanName:
    def test_normalizes_unicode(self):
        assert get_clean_name("café") == "café"

    def test_lowercases(self):
        assert get_clean_name("Hello World") == "helloworld"

    def test_removes_special_characters(self):
        assert get_clean_name("hello! @world#") == "helloworld"

    def test_empty_string(self):
        assert get_clean_name("") == ""

    def test_unicode_normalization(self):
        assert get_clean_name("Ñoño") == "ñoño"

    def test_removes_underscores(self):
        assert get_clean_name("hello_world") == "helloworld"


class TestConvertSecondsToReadableTime:
    def test_zero_seconds(self):
        assert convert_seconds_to_readable_time(0) == "00:00:00"

    def test_seconds_only(self):
        assert convert_seconds_to_readable_time(45) == "00:00:45"

    def test_minutes_and_seconds(self):
        assert convert_seconds_to_readable_time(125) == "00:02:05"

    def test_hours_minutes_seconds(self):
        assert convert_seconds_to_readable_time(3661) == "01:01:01"

    def test_large_value_wraps_at_24h(self):
        assert convert_seconds_to_readable_time(86400) == "00:00:00"

    def test_fractional_seconds(self):
        assert convert_seconds_to_readable_time(90.5) == "00:01:30"


class TestParseCronExpression:
    def test_valid_expression(self):
        result = parse_cron_expression("0 0 * * *")

        assert result == {
            "minute": "0",
            "hour": "0",
            "day": "*",
            "month": "*",
            "day_of_week": "*",
        }

    def test_weekly_expression(self):
        result = parse_cron_expression("0 0 * * 0")

        assert result["day_of_week"] == "0"

    def test_invalid_too_few_parts(self):
        with pytest.raises(ValueError, match="Invalid cron expression"):
            parse_cron_expression("0 0 *")

    def test_invalid_too_many_parts(self):
        with pytest.raises(ValueError, match="Invalid cron expression"):
            parse_cron_expression("0 0 * * * *")


class TestSanitizeFilename:
    def test_removes_illegal_characters(self):
        result = sanitize_filename('file:name"with<symbols>')

        assert ":" not in result
        assert '"' not in result
        assert "<" not in result
        assert ">" not in result

    def test_preserves_normal_text(self):
        assert sanitize_filename("hello world") == "hello world"

    def test_strips_whitespace(self):
        assert sanitize_filename("  hello  ") == "hello"

    def test_handles_unicode(self):
        result = sanitize_filename("café résumé")

        assert "é" not in result


class TestNormalize:
    def test_case_insensitive(self):
        assert normalize("Hello") == normalize("hello")

    def test_strips_whitespace(self):
        assert normalize("  hello  ") == "hello"

    def test_unicode_normalization(self):
        assert normalize("café") == "café"
        assert normalize("CAFÉ") == "café"

    def test_empty_string(self):
        assert normalize("") == ""


class TestTruncate:
    def test_no_truncation_needed(self):
        assert truncate("hello", 10) == "hello"

    def test_exact_length(self):
        assert truncate("hello", 5) == "hello"

    def test_truncation(self):
        assert truncate("hello world", 5) == "hello"

    def test_empty_string(self):
        assert truncate("", 5) == ""

    def test_zero_max_length(self):
        assert truncate("hello", 0) == ""
