# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for timestamp/interval parsing, spec parsing, and CLI in
reprostim.qr.split_video and reprostim.cli.cmd_split_video."""

import json
import os
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from reprostim.qr.split_video import (
    BufferPolicy,
    SpecEntry,
    SplitData,
    SplitResult,
    VideoSegment,
    _calc_split_data,
    _do_main_specs,
    _expand_output_template,
    _has_template_tokens,
    _parse_audio_info,
    _parse_interval_sec,
    _parse_spec,
    _parse_ts,
    _resolve_sidecar_path,
    _split_video,
    _write_sidecar,
    do_main,
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


# ===========================================================================
# Helpers for _calc_split_data tests
# ===========================================================================

# Video covers 2024-02-02 17:00:00 – 18:00:00 (3600 s, 30 fps, 1920x1080)
_VIDEO_START = datetime(2024, 2, 2, 17, 0, 0)
_VIDEO_END = datetime(2024, 2, 2, 18, 0, 0)


def _make_va_record():
    """Return a minimal VaRecord for a 1-hour test video."""
    from reprostim.qr.video_audit import VaRecord

    return VaRecord(
        path="/fake/video.mkv",
        present=True,
        start_date="2024-02-02",
        start_time="17:00:00",
        end_date="2024-02-02",
        end_time="18:00:00",
        duration="3600.0",
        video_fps_recorded="30",
        video_res_recorded="1920x1080",
        audio_sr="48000Hz 16b 2ch aac",
    )


# ===========================================================================
# _calc_split_data
# ===========================================================================


@patch("reprostim.qr.split_video.find_metadata_json", return_value=None)
@patch("reprostim.qr.split_video.get_file_video_audit")
def test_calc_split_data_basic(mock_gfva, _mock_fmj):
    """Basic: start + duration within video → correct SplitData."""
    mock_gfva.return_value = _make_va_record()

    sd = _calc_split_data(
        path="/fake/video.mkv",
        sel_start_ts=datetime(2024, 2, 2, 17, 30, 0),
        sel_duration_sec=180.0,
        sel_end_ts=None,
        buf_before_sec=0.0,
        buf_after_sec=0.0,
        buffer_policy=BufferPolicy.STRICT,
    )

    assert sd.success is True
    assert sd.sel_seg.start_ts == datetime(2024, 2, 2, 17, 30, 0)
    assert sd.sel_seg.end_ts == datetime(2024, 2, 2, 17, 33, 0)
    assert sd.sel_seg.duration_sec == pytest.approx(180.0)
    assert sd.sel_seg.offset_sec == pytest.approx(1800.0)
    assert sd.full_seg.start_ts == _VIDEO_START
    assert sd.full_seg.end_ts == _VIDEO_END


@patch("reprostim.qr.split_video.find_metadata_json", return_value=None)
@patch("reprostim.qr.split_video.get_file_video_audit")
def test_calc_split_data_buffer_trim_at_start_flexible(mock_gfva, _mock_fmj):
    """Flexible policy: buffer before trimmed when it extends before video start."""
    mock_gfva.return_value = _make_va_record()

    # Select starts 60 s into video; buffer before = 120 s (overflows by 60 s)
    sd = _calc_split_data(
        path="/fake/video.mkv",
        sel_start_ts=datetime(2024, 2, 2, 17, 1, 0),
        sel_duration_sec=60.0,
        sel_end_ts=None,
        buf_before_sec=120.0,
        buf_after_sec=0.0,
        buffer_policy=BufferPolicy.FLEXIBLE,
    )

    assert sd.success is True
    # Buffer start trimmed to video start
    assert sd.buf_seg.start_ts == _VIDEO_START
    assert sd.buf_seg.offset_sec == pytest.approx(0.0)


@patch("reprostim.qr.split_video.find_metadata_json", return_value=None)
@patch("reprostim.qr.split_video.get_file_video_audit")
def test_calc_split_data_buffer_trim_at_end_flexible(mock_gfva, _mock_fmj):
    """Flexible policy: buffer after trimmed when it extends past video end."""
    mock_gfva.return_value = _make_va_record()

    # Select ends 60 s before video end; buffer after = 120 s (overflows by 60 s)
    sd = _calc_split_data(
        path="/fake/video.mkv",
        sel_start_ts=datetime(2024, 2, 2, 17, 58, 0),
        sel_duration_sec=60.0,
        sel_end_ts=None,
        buf_before_sec=0.0,
        buf_after_sec=120.0,
        buffer_policy=BufferPolicy.FLEXIBLE,
    )

    assert sd.success is True
    # Buffer end trimmed to video end
    assert sd.buf_seg.end_ts == _VIDEO_END


@patch("reprostim.qr.split_video.find_metadata_json", return_value=None)
@patch("reprostim.qr.split_video.get_file_video_audit")
def test_calc_split_data_buffer_overflow_strict_raises(mock_gfva, _mock_fmj):
    """Strict policy: buffer overflow before video start raises ValueError."""
    mock_gfva.return_value = _make_va_record()

    with pytest.raises(ValueError, match="buffer.*before|before.*video"):
        _calc_split_data(
            path="/fake/video.mkv",
            sel_start_ts=datetime(2024, 2, 2, 17, 1, 0),
            sel_duration_sec=60.0,
            sel_end_ts=None,
            buf_before_sec=120.0,  # overflows video start
            buf_after_sec=0.0,
            buffer_policy=BufferPolicy.STRICT,
        )


@patch("reprostim.qr.split_video.find_metadata_json", return_value=None)
@patch("reprostim.qr.split_video.get_file_video_audit")
def test_calc_split_data_no_overlap_raises(mock_gfva, _mock_fmj):
    """Selected segment starting before video start raises ValueError."""
    mock_gfva.return_value = _make_va_record()

    with pytest.raises(ValueError, match="before video start"):
        _calc_split_data(
            path="/fake/video.mkv",
            sel_start_ts=datetime(2024, 2, 2, 16, 0, 0),  # before video start
            sel_duration_sec=60.0,
            sel_end_ts=None,
            buf_before_sec=0.0,
            buf_after_sec=0.0,
            buffer_policy=BufferPolicy.STRICT,
        )


# ===========================================================================
# _resolve_sidecar_path
# ===========================================================================

_RSP_START = datetime(2024, 2, 2, 17, 30, 0)
_RSP_END = datetime(2024, 2, 2, 17, 33, 0)
_RSP_DUR = 180.0


def test_resolve_sidecar_path_auto():
    """`auto` resolves to <output>.split-video.json."""
    result = _resolve_sidecar_path(
        "auto", "/out/clip.mkv", 1, _RSP_START, _RSP_END, _RSP_DUR
    )
    assert result == "/out/clip.mkv.split-video.json"


def test_resolve_sidecar_path_explicit_no_tokens():
    """Explicit path without template tokens is returned unchanged."""
    result = _resolve_sidecar_path(
        "/custom/meta.json", "/out/clip.mkv", 1, _RSP_START, _RSP_END, _RSP_DUR
    )
    assert result == "/custom/meta.json"


def test_resolve_sidecar_path_none_returns_none():
    """`None` input returns `None`."""
    result = _resolve_sidecar_path(
        None, "/out/clip.mkv", 1, _RSP_START, _RSP_END, _RSP_DUR
    )
    assert result is None


# ===========================================================================
# _write_sidecar
# ===========================================================================

_EXCLUDED_FIELDS = {"success", "input_path", "output_path", "start_time", "end_time"}
_EXPECTED_FIELDS = {
    "buffer_before",
    "buffer_after",
    "buffer_duration",
    "duration",
    "video_width",
    "video_height",
    "video_frame_rate",
    "orig_buffer_start",
    "orig_buffer_end",
    "orig_buffer_offset",
    "orig_start",
    "orig_end",
    "orig_offset",
    "orig_device",
    "orig_device_serial_number",
    "audio_sample_rate",
    "audio_bit_depth",
    "audio_channel_count",
    "audio_codec",
}


def _make_split_result() -> SplitResult:
    return SplitResult(
        success=True,
        input_path="/fake/input.mkv",
        output_path="/fake/output.mkv",
        buffer_before=5.0,
        buffer_after=5.0,
        buffer_duration=190.0,
        start_time=datetime(2024, 2, 2, 17, 30, 0),
        end_time=datetime(2024, 2, 2, 17, 33, 0),
        duration=180.0,
        video_width="1920",
        video_height="1080",
        video_frame_rate=30.0,
        video_size_mb=120.5,
        video_rate_mbpm=50.0,
        audio_sample_rate="48000",
        audio_bit_depth="16",
        audio_channel_count="2",
        audio_codec="aac",
        orig_buffer_start="17:25:00.000",
        orig_buffer_end="17:38:00.000",
        orig_buffer_offset=1500.0,
        orig_start="17:30:00.000",
        orig_end="17:33:00.000",
        orig_offset=1800.0,
        orig_device="TestDevice",
        orig_device_serial_number="SN-12345",
    )


def test_write_sidecar_expected_fields_present_excluded_absent():
    """All expected fields written; excluded fields absent from sidecar."""
    sr = _make_split_result()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        tmp_path = tmp.name

    try:
        _write_sidecar(tmp_path, sr)
        with open(tmp_path) as f:
            data = json.load(f)

        for field in _EXPECTED_FIELDS:
            assert field in data, f"Expected field '{field}' missing from sidecar"

        for field in _EXCLUDED_FIELDS:
            assert field not in data, f"Excluded field '{field}' found in sidecar"
    finally:
        os.unlink(tmp_path)


def test_write_sidecar_no_absolute_dates():
    """Sidecar JSON contains no absolute date strings (times only)."""
    sr = _make_split_result()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        tmp_path = tmp.name

    try:
        _write_sidecar(tmp_path, sr)
        with open(tmp_path) as f:
            raw = f.read()

        # No YYYY-MM-DD date patterns should appear in the sidecar
        import re

        date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")
        assert not date_pattern.search(
            raw
        ), "Sidecar contains absolute date string: " + str(date_pattern.findall(raw))
    finally:
        os.unlink(tmp_path)


# ===========================================================================
# Multi-spec mode (_do_main_specs)
# ===========================================================================

_MS_VIDEO_START = datetime(2024, 2, 2, 17, 0, 0)
_MS_VIDEO_END = datetime(2024, 2, 2, 18, 0, 0)


def _make_sd(
    start_hour: int = 17, start_min: int = 30, duration_s: float = 180.0
) -> SplitData:
    """Build a minimal successful SplitData for multi-spec tests."""
    sel_start = datetime(2024, 2, 2, start_hour, start_min, 0)
    sel_end = sel_start + timedelta(seconds=duration_s)
    buf_offset = (sel_start - _MS_VIDEO_START).total_seconds()
    return SplitData(
        success=True,
        path="/fake/video.mkv",
        fps=30.0,
        resolution="1920x1080",
        audio_sr="48000Hz 16b 2ch aac",
        full_seg=VideoSegment(
            start_ts=_MS_VIDEO_START,
            end_ts=_MS_VIDEO_END,
            offset_sec=0.0,
            duration_sec=3600.0,
        ),
        sel_seg=VideoSegment(
            start_ts=sel_start,
            end_ts=sel_end,
            offset_sec=buf_offset,
            duration_sec=duration_s,
        ),
        buf_seg=VideoSegment(
            start_ts=sel_start,
            end_ts=sel_end,
            offset_sec=buf_offset,
            duration_sec=duration_s,
        ),
    )


def _make_sr_ms(output_path: str = "/fake/output.mkv") -> SplitResult:
    """Build a minimal successful SplitResult for multi-spec tests."""
    return SplitResult(
        success=True,
        input_path="/fake/video.mkv",
        output_path=output_path,
        buffer_before=0.0,
        buffer_after=0.0,
        buffer_duration=180.0,
        duration=180.0,
        video_width="1920",
        video_height="1080",
        video_frame_rate=30.0,
        audio_sample_rate="48000",
        audio_bit_depth="16",
        audio_channel_count="2",
        audio_codec="aac",
        orig_buffer_start="17:30:00.000",
        orig_buffer_end="17:33:00.000",
        orig_buffer_offset=1800.0,
        orig_start="17:30:00.000",
        orig_end="17:33:00.000",
        orig_offset=1800.0,
        orig_device="n/a",
        orig_device_serial_number="n/a",
    )


@patch("reprostim.qr.split_video._split_video")
@patch("reprostim.qr.split_video._calc_split_data")
def test_do_main_specs_single_spec_output_used_as_is(mock_csd, mock_sv):
    """Single --spec: output path used as-is (no template expansion applied)."""
    mock_csd.return_value = _make_sd()
    mock_sv.return_value = _make_sr_ms(output_path="/out/clip.mkv")

    failures = _do_main_specs(
        specs=("2024-02-02T17:30:00/PT3M",),
        input_path="/fake/video.mkv",
        output_template="/out/clip.mkv",
        buffer_before=None,
        buffer_after=None,
        buffer_policy="strict",
        sidecar_json=None,
        video_audit_file=None,
        raw=False,
        verbose=False,
    )

    assert failures == 0
    mock_sv.assert_called_once()
    # Positional arg[1] is out_path; no tokens → unchanged
    assert mock_sv.call_args[0][1] == "/out/clip.mkv"


@patch("reprostim.qr.split_video._split_video")
@patch("reprostim.qr.split_video._calc_split_data")
def test_do_main_specs_multiple_specs_unique_output_files(mock_csd, mock_sv):
    """Multiple --spec with {n} token produces unique, indexed output paths."""
    mock_csd.side_effect = [_make_sd(17, 30), _make_sd(17, 40)]
    mock_sv.side_effect = [
        _make_sr_ms("/out/clip_001.mkv"),
        _make_sr_ms("/out/clip_002.mkv"),
    ]

    failures = _do_main_specs(
        specs=("2024-02-02T17:30:00/PT3M", "2024-02-02T17:40:00/PT3M"),
        input_path="/fake/video.mkv",
        output_template="/out/clip_{n}.mkv",
        buffer_before=None,
        buffer_after=None,
        buffer_policy="strict",
        sidecar_json=None,
        video_audit_file=None,
        raw=False,
        verbose=False,
    )

    assert failures == 0
    assert mock_sv.call_count == 2
    out_paths = [c[0][1] for c in mock_sv.call_args_list]
    assert "/out/clip_001.mkv" in out_paths
    assert "/out/clip_002.mkv" in out_paths


def test_do_main_specs_multiple_specs_no_template_token_raises():
    """Multiple --spec without a template token in output raises ValueError."""
    with pytest.raises(ValueError, match="template token"):
        _do_main_specs(
            specs=("2024-02-02T17:30:00/PT3M", "2024-02-02T17:40:00/PT3M"),
            input_path="/fake/video.mkv",
            output_template="/out/clip.mkv",  # no {n} token
            buffer_before=None,
            buffer_after=None,
            buffer_policy="strict",
            sidecar_json=None,
            video_audit_file=None,
            raw=False,
            verbose=False,
        )


@patch("reprostim.qr.split_video._split_video")
@patch("reprostim.qr.split_video._calc_split_data")
def test_do_main_specs_per_spec_failure_continues_processing(mock_csd, mock_sv):
    """Per-spec failure: remaining specs continue; return value
    reflects failure count."""
    mock_csd.side_effect = [ValueError("simulated failure"), _make_sd(17, 40)]
    mock_sv.return_value = _make_sr_ms("/out/clip_002.mkv")

    failures = _do_main_specs(
        specs=("2024-02-02T17:30:00/PT3M", "2024-02-02T17:40:00/PT3M"),
        input_path="/fake/video.mkv",
        output_template="/out/clip_{n}.mkv",
        buffer_before=None,
        buffer_after=None,
        buffer_policy="strict",
        sidecar_json=None,
        video_audit_file=None,
        raw=False,
        verbose=False,
    )

    assert failures == 1
    # Second spec still ran despite first failure
    mock_sv.assert_called_once()


# ===========================================================================
# CLI tests (Click CliRunner) for cmd_split_video
# ===========================================================================

from click.testing import CliRunner  # noqa: E402

from reprostim.cli.cmd_split_video import split_video  # noqa: E402


@pytest.fixture()
def input_video(tmp_path: Path) -> str:
    """Create a minimal placeholder file so Click's exists=True check passes."""
    f = tmp_path / "video.mkv"
    f.write_bytes(b"")
    return str(f)


def test_cli_help_renders_without_error():
    """--help exits with code 0 and produces output."""
    result = CliRunner().invoke(split_video, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_cli_missing_input_nonzero_exit():
    """Omitting --input produces a non-zero exit code with an error message."""
    result = CliRunner().invoke(split_video, ["--output", "out.mkv"])
    assert result.exit_code != 0
    assert "input" in result.output.lower() or "missing" in result.output.lower()


def test_cli_missing_output_nonzero_exit(input_video):
    """Omitting --output produces a non-zero exit code with an error message."""
    result = CliRunner().invoke(split_video, ["-i", input_video])
    assert result.exit_code != 0
    assert "output" in result.output.lower() or "missing" in result.output.lower()


def test_cli_spec_and_start_mutually_exclusive(input_video):
    """Providing both --spec and --start raises a UsageError."""
    result = CliRunner().invoke(
        split_video,
        [
            "-i",
            input_video,
            "-o",
            "out.mkv",
            "--spec",
            "2024-02-02T17:30:00/PT3M",
            "--start",
            "2024-02-02T17:30:00",
        ],
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()


def test_cli_duration_and_end_mutually_exclusive(input_video):
    """Providing both --duration and --end raises a UsageError."""
    result = CliRunner().invoke(
        split_video,
        [
            "-i",
            input_video,
            "-o",
            "out.mkv",
            "--start",
            "2024-02-02T17:30:00",
            "--duration",
            "180",
            "--end",
            "2024-02-02T17:33:00",
        ],
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()


def test_cli_neither_spec_nor_start_raises(input_video):
    """Providing neither --spec nor --start raises a UsageError."""
    result = CliRunner().invoke(
        split_video,
        ["-i", input_video, "-o", "out.mkv"],
    )
    assert result.exit_code != 0
    assert "--spec" in result.output or "--start" in result.output


def test_cli_lock_yes_passed_to_do_main(input_video):
    """--lock yes results in lock=True passed to do_main."""
    with patch("reprostim.qr.split_video.do_main", return_value=0) as mock_dm:
        CliRunner().invoke(
            split_video,
            [
                "-i",
                input_video,
                "-o",
                "out.mkv",
                "--spec",
                "2024-02-02T17:30:00/PT3M",
                "--lock",
                "yes",
            ],
        )
        mock_dm.assert_called_once()
        assert mock_dm.call_args.kwargs["lock"] is True


def test_cli_lock_no_passed_to_do_main(input_video):
    """--lock no results in lock=False passed to do_main."""
    with patch("reprostim.qr.split_video.do_main", return_value=0) as mock_dm:
        CliRunner().invoke(
            split_video,
            [
                "-i",
                input_video,
                "-o",
                "out.mkv",
                "--spec",
                "2024-02-02T17:30:00/PT3M",
                "--lock",
                "no",
            ],
        )
        mock_dm.assert_called_once()
        assert mock_dm.call_args.kwargs["lock"] is False


def test_cli_raw_flag_passed_to_do_main(input_video):
    """--raw flag results in raw=True passed to do_main."""
    with patch("reprostim.qr.split_video.do_main", return_value=0) as mock_dm:
        CliRunner().invoke(
            split_video,
            [
                "-i",
                input_video,
                "-o",
                "out.mkv",
                "--spec",
                "300/180",
                "--raw",
            ],
        )
        mock_dm.assert_called_once()
        assert mock_dm.call_args.kwargs["raw"] is True


# ===========================================================================
# _parse_audio_info
# ===========================================================================


def test_parse_audio_info_full_string():
    """Full audio info string parses all four fields correctly."""
    result = _parse_audio_info("48000Hz 16b 2ch aac")
    assert result["audio_sample_rate"] == "48000"
    assert result["audio_bit_depth"] == "16"
    assert result["audio_channel_count"] == "2"
    assert result["audio_codec"] == "aac"


def test_parse_audio_info_missing_bit_depth_defaults_to_16():
    """String without explicit bit depth defaults audio_bit_depth to '16'."""
    result = _parse_audio_info("48000Hz 2ch aac")
    assert result["audio_sample_rate"] == "48000"
    assert result["audio_bit_depth"] == "16"
    assert result["audio_channel_count"] == "2"
    assert result["audio_codec"] == "aac"


def test_parse_audio_info_none_returns_na():
    """None input returns all n/a fields."""
    result = _parse_audio_info(None)
    assert all(v == "n/a" for v in result.values())


def test_parse_audio_info_na_string_returns_na():
    """'n/a' string returns all n/a fields."""
    result = _parse_audio_info("n/a")
    assert all(v == "n/a" for v in result.values())


def test_parse_audio_info_empty_string_returns_na():
    """Empty string returns all n/a fields."""
    result = _parse_audio_info("")
    assert all(v == "n/a" for v in result.values())


def test_parse_audio_info_sample_rate_only():
    """String with only sample rate populates that field; others are n/a or default."""
    result = _parse_audio_info("44100Hz")
    assert result["audio_sample_rate"] == "44100"
    assert result["audio_bit_depth"] == "16"  # hardcoded default


# ===========================================================================
# _split_video
# ===========================================================================


def _fake_proc():
    """Return a mock subprocess.CompletedProcess-like object."""
    proc = MagicMock()
    proc.returncode = 0
    proc.stdout = ""
    proc.stderr = ""
    return proc


def test_split_video_success():
    """_split_video with mocked ffmpeg returns success=True and populates size/rate."""
    sd = _make_sd()
    with patch("subprocess.run", return_value=_fake_proc()), patch(
        "os.path.getsize", return_value=10 * 1024 * 1024
    ):
        sr = _split_video(sd, "/out/clip.mkv")

    assert sr.success is True
    assert sr.video_size_mb == pytest.approx(10.0)
    assert sr.video_rate_mbpm is not None
    assert sr.orig_start != "n/a"
    assert sr.orig_end != "n/a"
    assert sr.input_path == "/fake/video.mkv"
    assert sr.output_path == "/out/clip.mkv"


def test_split_video_ffmpeg_failure():
    """CalledProcessError from ffmpeg leaves success=False."""
    sd = _make_sd()
    with patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "ffmpeg"),
    ):
        sr = _split_video(sd, "/out/clip.mkv")

    assert sr.success is False


def test_split_video_resolution_na_gives_na_dimensions():
    """SplitData with resolution='n/a' produces video_width/height='n/a'."""
    sd = _make_sd()
    sd.resolution = "n/a"
    with patch("subprocess.run", return_value=_fake_proc()), patch(
        "os.path.getsize", return_value=1024
    ):
        sr = _split_video(sd, "/out/clip.mkv")

    assert sr.video_width == "n/a"
    assert sr.video_height == "n/a"


def test_split_video_resolution_none_gives_na_dimensions():
    """SplitData with resolution=None produces video_width/height='n/a'."""
    sd = _make_sd()
    sd.resolution = None
    with patch("subprocess.run", return_value=_fake_proc()), patch(
        "os.path.getsize", return_value=1024
    ):
        sr = _split_video(sd, "/out/clip.mkv")

    assert sr.video_width == "n/a"
    assert sr.video_height == "n/a"


# ===========================================================================
# do_main dispatch
# ===========================================================================


def test_do_main_start_duration_builds_spec():
    """do_main with start_time+duration builds a START/DURATION spec."""
    with patch("reprostim.qr.split_video._do_main_specs", return_value=0) as mock_dms:
        result = do_main(
            input_path="/fake/video.mkv",
            output_path="/out/clip.mkv",
            start_time="2024-02-02T17:30:00",
            duration="PT3M",
        )
    assert result == 0
    assert mock_dms.call_args.kwargs["specs"] == ("2024-02-02T17:30:00/PT3M",)


def test_do_main_start_end_builds_spec():
    """do_main with start_time+end_time builds a START//END spec."""
    with patch("reprostim.qr.split_video._do_main_specs", return_value=0) as mock_dms:
        result = do_main(
            input_path="/fake/video.mkv",
            output_path="/out/clip.mkv",
            start_time="2024-02-02T17:30:00",
            end_time="2024-02-02T17:33:00",
        )
    assert result == 0
    assert mock_dms.call_args.kwargs["specs"] == (
        "2024-02-02T17:30:00//2024-02-02T17:33:00",
    )


def test_do_main_specs_provided_directly():
    """do_main with specs tuple passes them straight to _do_main_specs."""
    with patch("reprostim.qr.split_video._do_main_specs", return_value=0) as mock_dms:
        result = do_main(
            input_path="/fake/video.mkv",
            output_path="/out/clip_{n}.mkv",
            specs=("2024-02-02T17:30:00/PT3M",),
        )
    assert result == 0
    assert mock_dms.call_args.kwargs["specs"] == ("2024-02-02T17:30:00/PT3M",)


def test_do_main_neither_spec_nor_start_returns_1():
    """do_main with no spec and no start_time returns exit code 1."""
    result = do_main(
        input_path="/fake/video.mkv",
        output_path="/out/clip.mkv",
    )
    assert result == 1


def test_do_main_value_error_from_specs_returns_5():
    """do_main returns 5 and emits ERROR when _do_main_specs raises ValueError."""
    messages = []
    with patch(
        "reprostim.qr.split_video._do_main_specs",
        side_effect=ValueError("bad template"),
    ):
        result = do_main(
            input_path="/fake/video.mkv",
            output_path="/out/clip.mkv",
            specs=("2024-02-02T17:30:00/PT3M",),
            out_func=messages.append,
        )
    assert result == 5
    assert any("ERROR" in m for m in messages)


# ===========================================================================
# _do_main_specs — remaining gap coverage
# ===========================================================================


@patch("reprostim.qr.split_video._split_video")
@patch("reprostim.qr.split_video._calc_split_data")
def test_do_main_specs_sd_success_false_counts_as_failure(mock_csd, mock_sv):
    """_calc_split_data returning success=False increments failure count."""
    sd = _make_sd()
    sd.success = False
    mock_csd.return_value = sd

    failures = _do_main_specs(
        specs=("2024-02-02T17:30:00/PT3M",),
        input_path="/fake/video.mkv",
        output_template="/out/clip.mkv",
        buffer_before=None,
        buffer_after=None,
        buffer_policy="strict",
        sidecar_json=None,
        video_audit_file=None,
        raw=False,
        verbose=False,
    )

    assert failures == 1
    mock_sv.assert_not_called()


@patch("reprostim.qr.split_video._split_video")
@patch("reprostim.qr.split_video._calc_split_data")
def test_do_main_specs_split_video_failure_counts(mock_csd, mock_sv):
    """_split_video returning success=False increments failure count."""
    mock_csd.return_value = _make_sd()
    sr = _make_sr_ms()
    sr.success = False
    mock_sv.return_value = sr

    failures = _do_main_specs(
        specs=("2024-02-02T17:30:00/PT3M",),
        input_path="/fake/video.mkv",
        output_template="/out/clip.mkv",
        buffer_before=None,
        buffer_after=None,
        buffer_policy="strict",
        sidecar_json=None,
        video_audit_file=None,
        raw=False,
        verbose=False,
    )

    assert failures == 1


@patch("reprostim.qr.split_video._split_video")
@patch("reprostim.qr.split_video._calc_split_data")
def test_do_main_specs_verbose_emits_output(mock_csd, mock_sv):
    """verbose=True causes spec progress lines to be emitted."""
    mock_csd.return_value = _make_sd()
    mock_sv.return_value = _make_sr_ms()

    output = []
    _do_main_specs(
        specs=("2024-02-02T17:30:00/PT3M",),
        input_path="/fake/video.mkv",
        output_template="/out/clip.mkv",
        buffer_before=None,
        buffer_after=None,
        buffer_policy="strict",
        sidecar_json=None,
        video_audit_file=None,
        raw=False,
        verbose=True,
        out_func=output.append,
    )

    assert any("Spec" in line for line in output)
    assert any("Input path" in line or "Output path" in line for line in output)


@patch("reprostim.qr.split_video._write_sidecar")
@patch("reprostim.qr.split_video._split_video")
@patch("reprostim.qr.split_video._calc_split_data")
def test_do_main_specs_sidecar_auto_written(mock_csd, mock_sv, mock_ws):
    """sidecar_json='auto' triggers _write_sidecar with a .split-video.json path."""
    mock_csd.return_value = _make_sd()
    mock_sv.return_value = _make_sr_ms()

    _do_main_specs(
        specs=("2024-02-02T17:30:00/PT3M",),
        input_path="/fake/video.mkv",
        output_template="/out/clip.mkv",
        buffer_before=None,
        buffer_after=None,
        buffer_policy="strict",
        sidecar_json="auto",
        video_audit_file=None,
        raw=False,
        verbose=False,
    )

    mock_ws.assert_called_once()
    sidecar_path_used = mock_ws.call_args[0][0]
    assert sidecar_path_used.endswith(".split-video.json")


def test_do_main_specs_sidecar_no_token_multiple_specs_raises():
    """Explicit sidecar path without template token raises
    ValueError for multiple specs."""
    with pytest.raises(ValueError, match="sidecar"):
        _do_main_specs(
            specs=("2024-02-02T17:30:00/PT3M", "2024-02-02T17:40:00/PT3M"),
            input_path="/fake/video.mkv",
            output_template="/out/clip_{n}.mkv",
            buffer_before=None,
            buffer_after=None,
            buffer_policy="strict",
            sidecar_json="/out/meta.json",  # no {n} token
            video_audit_file=None,
            raw=False,
            verbose=False,
        )


# ===========================================================================
# CLI — remaining gap coverage
# ===========================================================================


def test_cli_start_without_duration_or_end_raises(input_video):
    """--start without --duration or --end raises UsageError."""
    result = CliRunner().invoke(
        split_video,
        ["-i", input_video, "-o", "out.mkv", "--start", "2024-02-02T17:30:00"],
    )
    assert result.exit_code != 0
    assert "--duration" in result.output or "--end" in result.output


def test_cli_sidecar_json_auto_passed_to_do_main(input_video):
    """--sidecar-json auto passes sidecar_json='auto' to do_main."""
    with patch("reprostim.qr.split_video.do_main", return_value=0) as mock_dm:
        CliRunner().invoke(
            split_video,
            [
                "-i",
                input_video,
                "-o",
                "out.mkv",
                "--spec",
                "2024-02-02T17:30:00/PT3M",
                "--sidecar-json",
                "auto",
            ],
        )
    mock_dm.assert_called_once()
    assert mock_dm.call_args.kwargs["sidecar_json"] == "auto"


def test_cli_sidecar_json_explicit_path_passed_to_do_main(input_video):
    """Explicit --sidecar-json path is forwarded unchanged to do_main."""
    with patch("reprostim.qr.split_video.do_main", return_value=0) as mock_dm:
        CliRunner().invoke(
            split_video,
            [
                "-i",
                input_video,
                "-o",
                "out.mkv",
                "--spec",
                "2024-02-02T17:30:00/PT3M",
                "--sidecar-json",
                "/custom/meta.json",
            ],
        )
    mock_dm.assert_called_once()
    assert mock_dm.call_args.kwargs["sidecar_json"] == "/custom/meta.json"


def test_cli_verbose_emits_completed_message(input_video):
    """--verbose causes the 'completed' elapsed-time line to be echoed."""
    with patch("reprostim.qr.split_video.do_main", return_value=0):
        result = CliRunner().invoke(
            split_video,
            [
                "-i",
                input_video,
                "-o",
                "out.mkv",
                "--spec",
                "2024-02-02T17:30:00/PT3M",
                "--verbose",
            ],
        )
    assert "completed" in result.output.lower()
