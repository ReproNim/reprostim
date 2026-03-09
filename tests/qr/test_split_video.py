# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for timestamp/interval parsing and spec parsing in reprostim.qr.split_video."""

from datetime import datetime

import pytest

from reprostim.qr.split_video import (
    SpecEntry,
    _expand_output_template,
    _has_template_tokens,
    _parse_interval_sec,
    _parse_spec,
    _parse_ts,
)

# ===========================================================================
# _parse_ts
# ===========================================================================


def test_parse_ts_full_iso_datetime():
    """Full ISO 8601 datetime string is parsed to correct datetime."""
    dt = _parse_ts("2024-02-02T17:30:00")
    assert dt == datetime(2024, 2, 2, 17, 30, 0)


def test_parse_ts_full_iso_datetime_with_ms():
    """Full ISO 8601 datetime with milliseconds is parsed correctly."""
    dt = _parse_ts("2024-02-02T17:30:00.321")
    assert dt == datetime(2024, 2, 2, 17, 30, 0, 321000)


def test_parse_ts_time_only_returns_today_with_time():
    """Time-only string returns a datetime with today's date and the given time."""
    dt = _parse_ts("17:30:00", time_only=True)
    assert dt.hour == 17
    assert dt.minute == 30
    assert dt.second == 0


def test_parse_ts_time_only_with_T_prefix():
    """Time-only string with leading 'T' is handled correctly."""
    dt = _parse_ts("T17:30:00", time_only=True)
    assert dt.hour == 17
    assert dt.minute == 30
    assert dt.second == 0


def test_parse_ts_numeric_seconds_offset():
    """Numeric seconds string is converted to a datetime offset from midnight."""
    dt = _parse_ts("300")
    assert dt.hour == 0
    assert dt.minute == 5
    assert dt.second == 0


def test_parse_ts_numeric_seconds_float():
    """Numeric float seconds string is converted correctly."""
    dt = _parse_ts("3661.5")
    assert dt.hour == 1
    assert dt.minute == 1
    assert dt.second == 1


def test_parse_ts_none_returns_none():
    """None input returns None."""
    assert _parse_ts(None) is None


def test_parse_ts_empty_string_returns_none():
    """Empty string returns None."""
    assert _parse_ts("") is None


def test_parse_ts_invalid_raises_value_error():
    """Invalid time string raises ValueError."""
    with pytest.raises(ValueError):
        _parse_ts("not-a-time")


# ===========================================================================
# _parse_interval_sec
# ===========================================================================


def test_parse_interval_sec_float_string():
    """Plain float string is returned as float seconds."""
    assert _parse_interval_sec("180.0") == pytest.approx(180.0)


def test_parse_interval_sec_integer_string():
    """Integer seconds string is returned as float."""
    assert _parse_interval_sec("60") == pytest.approx(60.0)


def test_parse_interval_sec_iso8601_minutes():
    """ISO 8601 duration PT3M is parsed to 180 seconds."""
    assert _parse_interval_sec("PT3M") == pytest.approx(180.0)


def test_parse_interval_sec_iso8601_hours_minutes():
    """ISO 8601 duration PT1H30M is parsed to 5400 seconds."""
    assert _parse_interval_sec("PT1H30M") == pytest.approx(5400.0)


def test_parse_interval_sec_iso8601_seconds():
    """ISO 8601 duration PT10S is parsed to 10 seconds."""
    assert _parse_interval_sec("PT10S") == pytest.approx(10.0)


def test_parse_interval_sec_empty_returns_zero():
    """Empty string returns 0.0."""
    assert _parse_interval_sec("") == pytest.approx(0.0)


def test_parse_interval_sec_na_returns_zero():
    """'n/a' string returns 0.0."""
    assert _parse_interval_sec("n/a") == pytest.approx(0.0)


def test_parse_interval_sec_invalid_raises_value_error():
    """Non-numeric, non-ISO string raises ValueError."""
    with pytest.raises(ValueError):
        _parse_interval_sec("not-a-duration")


# ===========================================================================
# _parse_spec
# ===========================================================================


def test_parse_spec_start_duration_format():
    """START/DURATION format is parsed to SpecEntry with duration_str set."""
    entry = _parse_spec("2024-02-02T17:30:00/PT3M")
    assert isinstance(entry, SpecEntry)
    assert entry.start_str == "2024-02-02T17:30:00"
    assert entry.duration_str == "PT3M"
    assert entry.end_str is None


def test_parse_spec_start_end_format():
    """START//END format is parsed to SpecEntry with end_str set."""
    entry = _parse_spec("2024-02-02T17:30:00//2024-02-02T17:33:00")
    assert isinstance(entry, SpecEntry)
    assert entry.start_str == "2024-02-02T17:30:00"
    assert entry.end_str == "2024-02-02T17:33:00"
    assert entry.duration_str is None


def test_parse_spec_time_only_start_with_iso_duration():
    """Time-only start with ISO 8601 duration is parsed correctly."""
    entry = _parse_spec("17:30:00/PT3M")
    assert entry.start_str == "17:30:00"
    assert entry.duration_str == "PT3M"
    assert entry.end_str is None


def test_parse_spec_numeric_seconds_start_and_duration():
    """Numeric seconds for both start and duration are parsed correctly."""
    entry = _parse_spec("300/180")
    assert entry.start_str == "300"
    assert entry.duration_str == "180"
    assert entry.end_str is None


def test_parse_spec_time_only_start_end():
    """Time-only START//END format is parsed correctly."""
    entry = _parse_spec("17:30:00//17:33:00")
    assert entry.start_str == "17:30:00"
    assert entry.end_str == "17:33:00"
    assert entry.duration_str is None


def test_parse_spec_invalid_no_slash_raises_error():
    """Spec without '/' raises ValueError."""
    with pytest.raises(ValueError):
        _parse_spec("17:30:00")


def test_parse_spec_empty_start_raises_error():
    """Empty start part raises ValueError."""
    with pytest.raises(ValueError):
        _parse_spec("/PT3M")


def test_parse_spec_empty_duration_raises_error():
    """Empty duration part raises ValueError."""
    with pytest.raises(ValueError):
        _parse_spec("17:30:00/")


def test_parse_spec_empty_end_raises_error():
    """Empty end part in START//END format raises ValueError."""
    with pytest.raises(ValueError):
        _parse_spec("17:30:00//")


# ===========================================================================
# _has_template_tokens
# ===========================================================================


def test_has_template_tokens_with_n():
    """String containing {n} returns True."""
    assert _has_template_tokens("output_{n}.mkv") is True


def test_has_template_tokens_with_start():
    """String containing {start} returns True."""
    assert _has_template_tokens("output_{start}.mkv") is True


def test_has_template_tokens_with_end():
    """String containing {end} returns True."""
    assert _has_template_tokens("clip_{end}.mkv") is True


def test_has_template_tokens_with_duration():
    """String containing {duration} returns True."""
    assert _has_template_tokens("clip_{duration}.mkv") is True


def test_has_template_tokens_no_tokens():
    """String with no template tokens returns False."""
    assert _has_template_tokens("output.mkv") is False


def test_has_template_tokens_empty_string():
    """Empty string returns False."""
    assert _has_template_tokens("") is False


# ===========================================================================
# _expand_output_template
# ===========================================================================

_START_DT = datetime(2024, 2, 2, 17, 30, 0)
_END_DT = datetime(2024, 2, 2, 17, 33, 0)
_DURATION = 180.0


def test_expand_output_template_n_token():
    """{n} is replaced with zero-padded 3-digit index."""
    result = _expand_output_template("output_{n}.mkv", 1, _START_DT, _END_DT, _DURATION)
    assert result == "output_001.mkv"


def test_expand_output_template_n_token_large_index():
    """{n} with index > 999 still expands (no truncation)."""
    result = _expand_output_template("output_{n}.mkv", 5, _START_DT, _END_DT, _DURATION)
    assert result == "output_005.mkv"


def test_expand_output_template_start_token():
    """{start} is replaced with dot-formatted start time."""
    result = _expand_output_template(
        "clip_{start}.mkv", 1, _START_DT, _END_DT, _DURATION
    )
    assert result == "clip_17.30.00.000.mkv"


def test_expand_output_template_end_token():
    """{end} is replaced with dot-formatted end time."""
    result = _expand_output_template("clip_{end}.mkv", 1, _START_DT, _END_DT, _DURATION)
    assert result == "clip_17.33.00.000.mkv"


def test_expand_output_template_duration_token():
    """{duration} is replaced with duration in seconds."""
    result = _expand_output_template(
        "clip_{duration}.mkv", 1, _START_DT, _END_DT, _DURATION
    )
    assert result == "clip_180.0.mkv"


def test_expand_output_template_all_tokens():
    """All tokens are expanded correctly in a single template."""
    result = _expand_output_template(
        "{n}_{start}_{end}_{duration}.mkv", 2, _START_DT, _END_DT, _DURATION
    )
    assert result == "002_17.30.00.000_17.33.00.000_180.0.mkv"


def test_expand_output_template_no_tokens():
    """Template without tokens is returned unchanged."""
    result = _expand_output_template("output.mkv", 1, _START_DT, _END_DT, _DURATION)
    assert result == "output.mkv"
