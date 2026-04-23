# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""CLI tests for ``reprostim video-audit``.

Covers: --nosignal-opts, --qr-opts, --config and their default behaviour.
``do_main`` is patched so no real video processing takes place.
"""

import json
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import click.testing
import pytest

from reprostim.cli.cmd_video_audit import video_audit
from reprostim.qr.video_audit import (
    VaContext,
    VaMode,
    VaRecord,
    VaSource,
    _compare_rec_ts,
    _load_tsv,
    _match_recs,
    _merge_rec,
    _merge_recs,
    _parse_rec_datetime,
    _save_tsv,
    check_coherent,
    check_ffprobe,
    find_metadata_json,
    find_video_audit_by_timerange,
    format_date,
    format_duration,
    format_time,
    iter_metadata_json,
)

runner = click.testing.CliRunner()

# Timestamp constants used across merge/compare tests
_TS_EARLY = "2025-01-01 00:00:00.000000"
_TS_LATE = "2025-01-01 01:00:00.000000"

# Env var required by do_main / get_file_video_audit
_ENV = {"REPROSTIM_LOG_LEVEL": "INFO"}


def _rec(name="a.mkv", **kw) -> VaRecord:
    """Minimal VaRecord for unit tests."""
    return VaRecord(name=name, path=kw.pop("path", f"/data/{name}"), **kw)


def _ctx(**kw) -> VaContext:
    """VaContext with safe defaults for unit tests."""
    defaults = dict(
        c_internal=0,
        c_nosignal=0,
        c_qr=0,
        log_level="INFO",
        max_counter=-1,
        mode=VaMode.INCREMENTAL,
        source={VaSource.INTERNAL},
        recursive=False,
        path_mask=None,
        skip_names=None,
        updated_paths=set(),
    )
    defaults.update(kw)
    return VaContext(**defaults)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_mkv(tmp_path):
    """Return a path to an empty .mkv file accepted by click.Path(exists=True)."""
    p = tmp_path / "test.mkv"
    p.touch()
    return str(p)


def _invoke(args):
    """Invoke the video_audit command and return the result."""
    return runner.invoke(video_audit, args, catch_exceptions=False)


# ---------------------------------------------------------------------------
# --help
# ---------------------------------------------------------------------------


def test_help_renders():
    """--help exits cleanly and lists all key options."""
    result = runner.invoke(video_audit, ["--help"])
    assert result.exit_code == 0
    for flag in ("--nosignal-opts", "--qr-opts", "--config", "--mode", "--audit-src"):
        assert flag in result.output


# ---------------------------------------------------------------------------
# --nosignal-opts / -n
# ---------------------------------------------------------------------------


def test_nosignal_opts_forwarded(tmp_mkv):
    """-n / --nosignal-opts value is forwarded to do_main as nosignal_opts kwarg."""
    opts = "--number-of-checks 200 --threshold 0.9"
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-n", opts, tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["nosignal_opts"] == opts


def test_nosignal_opts_short_form_forwarded(tmp_mkv):
    """Short form -n is accepted and forwards the value identically
    to --nosignal-opts."""
    opts = "--number-of-checks 50"
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["--nosignal-opts", opts, tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["nosignal_opts"] == opts


def test_nosignal_opts_default_is_none(tmp_mkv):
    """Omitting --nosignal-opts passes nosignal_opts=None so VaContext uses
    built-in defaults."""
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke([tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["nosignal_opts"] is None


# ---------------------------------------------------------------------------
# --qr-opts / -q
# ---------------------------------------------------------------------------


def test_qr_opts_forwarded(tmp_mkv):
    """-q / --qr-opts value is forwarded to do_main as qr_opts kwarg."""
    opts = "--skip 2 --std-threshold 15"
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-q", opts, tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["qr_opts"] == opts


def test_qr_opts_short_form_forwarded(tmp_mkv):
    """Short form -q is accepted and forwards the value identically to --qr-opts."""
    opts = "--skip 4"
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["--qr-opts", opts, tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["qr_opts"] == opts


def test_qr_opts_default_is_none(tmp_mkv):
    """Omitting --qr-opts passes qr_opts=None so no extra options are forwarded."""
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke([tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["qr_opts"] is None


# ---------------------------------------------------------------------------
# -c / --config
# ---------------------------------------------------------------------------


def test_config_nosignal_opts(tmp_path, tmp_mkv):
    """nosignal-opts from config file is forwarded to do_main as nosignal_opts."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("nosignal-opts: '--number-of-checks 300 --threshold 0.8'\n")
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-c", str(cfg), tmp_mkv])
    assert result.exit_code == 0
    assert (
        mock_do_main.call_args.kwargs["nosignal_opts"]
        == "--number-of-checks 300 --threshold 0.8"
    )


def test_config_qr_opts(tmp_path, tmp_mkv):
    """qr-opts from config file is forwarded to do_main as qr_opts."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("qr-opts: '--skip 3 --std-threshold 20'\n")
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-c", str(cfg), tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["qr_opts"] == "--skip 3 --std-threshold 20"


def test_config_cli_overrides_nosignal_opts(tmp_path, tmp_mkv):
    """Explicit -n on CLI takes precedence over nosignal-opts in config."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("nosignal-opts: '--number-of-checks 300'\n")
    cli_opts = "--number-of-checks 999"
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-c", str(cfg), "-n", cli_opts, tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["nosignal_opts"] == cli_opts


def test_config_cli_overrides_qr_opts(tmp_path, tmp_mkv):
    """Explicit -q on CLI takes precedence over qr-opts in config."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("qr-opts: '--skip 3'\n")
    cli_opts = "--skip 99"
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-c", str(cfg), "-q", cli_opts, tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["qr_opts"] == cli_opts


def test_config_other_keys(tmp_path, tmp_mkv):
    """mode, recursive, and max-files from config are passed correctly to do_main."""
    from reprostim.qr.video_audit import VaMode

    cfg = tmp_path / "config.yaml"
    cfg.write_text("mode: full\nrecursive: true\nmax-files: 5\n")
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-c", str(cfg), tmp_mkv])
    assert result.exit_code == 0
    args = mock_do_main.call_args.args
    assert args[2] is True  # recursive
    assert args[3] == VaMode.FULL  # mode
    assert args[5] == 5  # max_files


def test_config_audit_src_list(tmp_path, tmp_mkv):
    """audit-src list in config is converted to a set of VaSource values."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("audit-src:\n  - internal\n  - qr\n")
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-c", str(cfg), tmp_mkv])
    assert result.exit_code == 0
    va_src = mock_do_main.call_args.args[4]
    assert va_src == {VaSource.INTERNAL, VaSource.QR}


# ---------------------------------------------------------------------------
# CLI: config audit-src scalar string / --mode / unknown mode
# ---------------------------------------------------------------------------


def test_config_audit_src_scalar_string(tmp_path, tmp_mkv):
    """Config audit-src as a scalar string is wrapped into a single-element tuple."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("audit-src: qr\n")
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-c", str(cfg), tmp_mkv])
    assert result.exit_code == 0
    va_src = mock_do_main.call_args.args[4]
    assert va_src == {VaSource.QR}


def test_mode_full_passed_to_do_main(tmp_mkv):
    """--mode full passes VaMode.FULL as the mode positional arg to do_main."""
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["--mode", "full", tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.args[3] == VaMode.FULL


def test_unknown_mode_click_error(tmp_mkv):
    """An invalid --mode value causes Click to exit with a non-zero code."""
    result = runner.invoke(video_audit, ["--mode", "bogus", tmp_mkv])
    assert result.exit_code != 0


# ===========================================================================
# format_duration
# ===========================================================================


def test_format_duration_none():
    assert format_duration(None) == "n/a"


def test_format_duration_zero():
    assert format_duration(0) == "00:00:00.000"


def test_format_duration_sub_minute():
    assert format_duration(45.5) == "00:00:45.500"


def test_format_duration_hours():
    assert format_duration(3723.0) == "01:02:03.000"


# ===========================================================================
# format_date / format_time
# ===========================================================================


def test_format_date_none():
    assert format_date(None) == "n/a"


def test_format_date_known():
    assert format_date(datetime(2025, 3, 15, 10, 30, 45)) == "2025-03-15"


def test_format_time_none():
    assert format_time(None) == "n/a"


def test_format_time_known():
    assert format_time(datetime(2025, 3, 15, 10, 30, 45, 123000)) == "10:30:45.123"


# ===========================================================================
# check_coherent
# ===========================================================================


def _coherent_rec(**kw) -> VaRecord:
    defaults = dict(
        path="/data/test.mkv",
        name="test.mkv",
        present=True,
        complete=True,
        start_date="2025-01-01",
        start_time="00:00:00.000",
        end_date="2025-01-01",
        end_time="00:01:00.000",
        video_res_detected="1920x1080",
        video_fps_detected="30.0",
        video_res_recorded="1920x1080",
        video_fps_recorded="30.0",
        duration="60.0",
        duration_h="00:01:00.000",
    )
    defaults.update(kw)
    return VaRecord(**defaults)


def test_check_coherent_valid():
    assert check_coherent(_coherent_rec()) is True


def test_check_coherent_not_present():
    assert check_coherent(_coherent_rec(present=False)) is False


def test_check_coherent_not_complete():
    assert check_coherent(_coherent_rec(complete=False)) is False


def test_check_coherent_missing_start():
    assert check_coherent(_coherent_rec(start_date="n/a")) is False


def test_check_coherent_missing_end():
    assert check_coherent(_coherent_rec(end_date="n/a")) is False


def test_check_coherent_missing_detected_res():
    assert check_coherent(_coherent_rec(video_res_detected="n/a")) is False


def test_check_coherent_missing_recorded_res():
    assert check_coherent(_coherent_rec(video_res_recorded="n/a")) is False


def test_check_coherent_missing_duration():
    assert check_coherent(_coherent_rec(duration="n/a")) is False


def test_check_coherent_res_mismatch():
    assert check_coherent(_coherent_rec(video_res_detected="1280x720")) is False


def test_check_coherent_fps_mismatch():
    assert check_coherent(_coherent_rec(video_fps_detected="25.0")) is False


# ===========================================================================
# check_ffprobe
# ===========================================================================


def test_check_ffprobe_available():
    with patch("reprostim.qr.video_audit.subprocess.run"):
        assert check_ffprobe() is True


def test_check_ffprobe_not_found():
    with patch(
        "reprostim.qr.video_audit.subprocess.run", side_effect=FileNotFoundError
    ):
        assert check_ffprobe() is False


# ===========================================================================
# _compare_rec_ts
# ===========================================================================


def test_compare_rec_ts_both_na():
    assert _compare_rec_ts(_rec(updated_on="n/a"), _rec(updated_on="n/a")) == 0


def test_compare_rec_ts_equal():
    assert _compare_rec_ts(_rec(updated_on=_TS_EARLY), _rec(updated_on=_TS_EARLY)) == 0


def test_compare_rec_ts_left_na():
    assert _compare_rec_ts(_rec(updated_on="n/a"), _rec(updated_on=_TS_EARLY)) == -1


def test_compare_rec_ts_right_na():
    assert _compare_rec_ts(_rec(updated_on=_TS_EARLY), _rec(updated_on="n/a")) == 1


def test_compare_rec_ts_earlier():
    assert _compare_rec_ts(_rec(updated_on=_TS_EARLY), _rec(updated_on=_TS_LATE)) == -1


def test_compare_rec_ts_later():
    assert _compare_rec_ts(_rec(updated_on=_TS_LATE), _rec(updated_on=_TS_EARLY)) == 1


# ===========================================================================
# _match_recs
# ===========================================================================


def test_match_recs_identical():
    r = _rec()
    assert _match_recs([r], [r]) is True


def test_match_recs_different_length():
    assert _match_recs([_rec()], []) is False


def test_match_recs_different_content():
    assert _match_recs([_rec(name="a.mkv")], [_rec(name="b.mkv")]) is False


# ===========================================================================
# _merge_rec
# ===========================================================================


def test_merge_rec_all_equal_returns_new():
    r_cur = _rec(
        updated_on=_TS_EARLY, no_signal_updated_on=_TS_EARLY, qr_updated_on=_TS_EARLY
    )
    r_new = _rec(
        updated_on=_TS_EARLY, no_signal_updated_on=_TS_EARLY, qr_updated_on=_TS_EARLY
    )
    result = _merge_rec(_ctx(), r_cur, r_new)
    assert result is r_new


def test_merge_rec_newer_internal_in_new():
    r_cur = _rec(updated_on=_TS_EARLY, no_signal_updated_on="n/a", qr_updated_on="n/a")
    r_new = _rec(updated_on=_TS_LATE, no_signal_updated_on="n/a", qr_updated_on="n/a")
    result = _merge_rec(_ctx(), r_cur, r_new)
    assert result.updated_on == _TS_LATE


def test_merge_rec_newer_nosignal_in_cur():
    r_cur = _rec(
        no_signal_frames="5.0",
        no_signal_updated_on=_TS_LATE,
        updated_on=_TS_EARLY,
        qr_updated_on="n/a",
    )
    r_new = _rec(
        no_signal_frames="9.0",
        no_signal_updated_on=_TS_EARLY,
        updated_on=_TS_LATE,
        qr_updated_on="n/a",
    )
    result = _merge_rec(_ctx(), r_cur, r_new)
    assert result.no_signal_frames == "5.0"


def test_merge_rec_newer_qr_in_new():
    r_cur = _rec(
        qr_records_number="10",
        qr_updated_on=_TS_EARLY,
        updated_on="n/a",
        no_signal_updated_on="n/a",
    )
    r_new = _rec(
        qr_records_number="20",
        qr_updated_on=_TS_LATE,
        updated_on="n/a",
        no_signal_updated_on="n/a",
    )
    result = _merge_rec(_ctx(), r_cur, r_new)
    assert result.qr_records_number == "20"


# ===========================================================================
# _merge_recs
# ===========================================================================


def test_merge_recs_no_change_skips_merge():
    """When recs0 == recs_cur the merge step is skipped and recs_new returned as-is."""
    r = _rec(updated_on=_TS_EARLY)
    result = _merge_recs(_ctx(), [r], [r], [r])
    assert result == [r]


def test_merge_recs_full_mode_overrides():
    r_old = _rec(name="a.mkv", updated_on=_TS_EARLY)
    r_cur = _rec(name="a.mkv", updated_on=_TS_LATE)
    r_new = _rec(name="b.mkv", updated_on=_TS_EARLY)
    result = _merge_recs(_ctx(mode=VaMode.FULL), [r_old], [r_cur], [r_new])
    assert result == [r_new]


def test_merge_recs_force_mode_merges_all():
    r_old = _rec(name="a.mkv", updated_on=_TS_EARLY)
    r_cur = _rec(name="a.mkv", updated_on=_TS_LATE)
    r_new = _rec(name="b.mkv", updated_on=_TS_EARLY)
    result = _merge_recs(_ctx(mode=VaMode.FORCE), [r_old], [r_cur], [r_new])
    names = {r.name for r in result}
    assert "a.mkv" in names and "b.mkv" in names


def test_merge_recs_incremental_timestamp_wins():
    """In incremental mode the newer timestamp between cur and new wins."""
    r_old = _rec(name="a.mkv", updated_on=_TS_EARLY)
    r_cur = _rec(name="a.mkv", updated_on=_TS_LATE)
    r_new = _rec(name="a.mkv", updated_on=_TS_EARLY)
    result = _merge_recs(_ctx(mode=VaMode.INCREMENTAL), [r_old], [r_cur], [r_new])
    assert result[0].updated_on == _TS_LATE


# ===========================================================================
# TSV I/O
# ===========================================================================


def test_save_load_tsv_roundtrip(tmp_path):
    recs = [_rec(name="a.mkv"), _rec(name="b.mkv")]
    path = str(tmp_path / "videos.tsv")
    _save_tsv(recs, path)
    loaded = _load_tsv(path)
    assert [r.name for r in loaded] == ["a.mkv", "b.mkv"]


def test_get_tsv_records_with_lock(tmp_path):
    from reprostim.qr.video_audit import _get_tsv_records, _tsv_cache

    path = str(tmp_path / "videos.tsv")
    _save_tsv([_rec(name="x.mkv")], path)
    _tsv_cache.pop(path, None)
    assert _get_tsv_records(path, use_lock=True)[0].name == "x.mkv"


def test_get_tsv_records_no_lock(tmp_path):
    from reprostim.qr.video_audit import _get_tsv_records, _tsv_cache

    path = str(tmp_path / "videos.tsv")
    _save_tsv([_rec(name="y.mkv")], path)
    _tsv_cache.pop(path, None)
    assert _get_tsv_records(path, use_lock=False)[0].name == "y.mkv"


def test_get_tsv_records_cached(tmp_path):
    from reprostim.qr.video_audit import _get_tsv_records, _tsv_cache

    path = str(tmp_path / "videos.tsv")
    _save_tsv([_rec(name="z.mkv")], path)
    _tsv_cache.pop(path, None)
    _get_tsv_records(path, cached=True)
    _save_tsv([_rec(name="new.mkv")], path)
    cached = _get_tsv_records(path, cached=True)
    assert cached[0].name == "z.mkv"


# ===========================================================================
# iter_metadata_json / find_metadata_json
# ===========================================================================


def _write_log(tmp_path, entries):
    log = tmp_path / "test.log"
    lines = [
        f"PREFIX REPROSTIM-METADATA-JSON: {json.dumps(e)} :REPROSTIM-METADATA-JSON\n"
        for e in entries
    ]
    log.write_text("".join(lines))
    return str(log)


def test_iter_metadata_json_valid(tmp_path):
    path = _write_log(tmp_path, [{"type": "session_begin", "cx": 1920}])
    results = list(iter_metadata_json(path))
    assert len(results) == 1
    assert results[0]["cx"] == 1920


def test_iter_metadata_json_missing_file(tmp_path):
    assert list(iter_metadata_json(str(tmp_path / "missing.log"))) == []


def test_find_metadata_json_found(tmp_path):
    path = _write_log(tmp_path, [{"type": "session_begin", "cx": 1920}])
    result = find_metadata_json(path, "type", "session_begin")
    assert result is not None and result["cx"] == 1920


def test_find_metadata_json_not_found(tmp_path):
    log = tmp_path / "empty.log"
    log.write_text("no metadata here\n")
    assert find_metadata_json(str(log), "type", "session_begin") is None


# ===========================================================================
# _parse_rec_datetime
# ===========================================================================


def test_parse_rec_datetime_valid():
    dt = _parse_rec_datetime("2025-01-15", "10:30:45.123")
    assert dt is not None and dt.year == 2025 and dt.hour == 10


def test_parse_rec_datetime_na_date():
    assert _parse_rec_datetime("n/a", "10:30:45.123") is None


def test_parse_rec_datetime_na_time():
    assert _parse_rec_datetime("2025-01-15", "n/a") is None


# ===========================================================================
# find_video_audit_by_timerange
# ===========================================================================


def _range_rec(name, start: datetime, end: datetime) -> VaRecord:
    return VaRecord(
        name=name,
        path=f"/data/{name}",
        present=True,
        complete=True,
        start_date=start.strftime("%Y-%m-%d"),
        start_time=start.strftime("%H:%M:%S.") + f"{start.microsecond // 1000:03d}",
        end_date=end.strftime("%Y-%m-%d"),
        end_time=end.strftime("%H:%M:%S.") + f"{end.microsecond // 1000:03d}",
    )


def _tsv_with(tmp_path, records):
    path = str(tmp_path / "videos.tsv")
    _save_tsv(records, path)
    return path


def test_find_video_audit_intersects(tmp_path):
    r = _range_rec("a.mkv", datetime(2025, 1, 1, 10, 0), datetime(2025, 1, 1, 11, 0))
    path = _tsv_with(tmp_path, [r])
    result = find_video_audit_by_timerange(
        path, datetime(2025, 1, 1, 10, 30), datetime(2025, 1, 1, 12, 0), use_lock=False
    )
    assert len(result) == 1 and result[0].name == "a.mkv"


def test_find_video_audit_before_range(tmp_path):
    r = _range_rec("a.mkv", datetime(2025, 1, 1, 8, 0), datetime(2025, 1, 1, 9, 0))
    path = _tsv_with(tmp_path, [r])
    result = find_video_audit_by_timerange(
        path, datetime(2025, 1, 1, 10, 0), datetime(2025, 1, 1, 11, 0), use_lock=False
    )
    assert result == []


def test_find_video_audit_after_range(tmp_path):
    r = _range_rec("a.mkv", datetime(2025, 1, 1, 12, 0), datetime(2025, 1, 1, 13, 0))
    path = _tsv_with(tmp_path, [r])
    result = find_video_audit_by_timerange(
        path, datetime(2025, 1, 1, 10, 0), datetime(2025, 1, 1, 11, 0), use_lock=False
    )
    assert result == []


def test_find_video_audit_sorted_ascending(tmp_path):
    r1 = _range_rec("b.mkv", datetime(2025, 1, 1, 11, 0), datetime(2025, 1, 1, 12, 0))
    r2 = _range_rec("a.mkv", datetime(2025, 1, 1, 10, 0), datetime(2025, 1, 1, 11, 30))
    path = _tsv_with(tmp_path, [r1, r2])
    result = find_video_audit_by_timerange(
        path, datetime(2025, 1, 1, 9, 0), datetime(2025, 1, 1, 13, 0), use_lock=False
    )
    assert result[0].name == "a.mkv" and result[1].name == "b.mkv"


# ===========================================================================
# _build_dated_path
# ===========================================================================


def test_build_dated_path_with_date(tmp_path):
    from reprostim.qr.video_audit import _build_dated_path

    r = _rec(name="video.mkv", path="/data/video.mkv", start_date="2025-03-15")
    result = _build_dated_path(r, str(tmp_path), "nosignal.json")
    assert "2025" in result and "03" in result
    assert result.endswith("video.mkv.nosignal.json")


def test_build_dated_path_na_date(tmp_path):
    from reprostim.qr.video_audit import _build_dated_path

    r = _rec(name="video.mkv", path="/data/video.mkv", start_date="n/a")
    result = _build_dated_path(r, str(tmp_path), "nosignal.json")
    assert result.endswith("video.mkv.nosignal.json")
    assert "n/a" not in result


# ===========================================================================
# do_audit_file
# ===========================================================================


def test_do_audit_file_max_counter(tmp_path):
    from reprostim.qr.video_audit import do_audit_file

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    assert list(do_audit_file(_ctx(max_counter=0, c_internal=0), str(mkv))) == []


def test_do_audit_file_skip_by_path(tmp_path):
    from reprostim.qr.video_audit import do_audit_file

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    assert list(do_audit_file(_ctx(skip_names={str(mkv)}), str(mkv))) == []


def test_do_audit_file_path_mask_no_match(tmp_path):
    from reprostim.qr.video_audit import do_audit_file

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    assert list(do_audit_file(_ctx(path_mask="*/other/*.mkv"), str(mkv))) == []


def test_do_audit_file_missing_file(tmp_path):
    from reprostim.qr.video_audit import do_audit_file

    records = list(do_audit_file(_ctx(), str(tmp_path / "missing.mkv")))
    assert len(records) == 1 and records[0].present is False


def test_do_audit_file_happy_path(tmp_path):
    from reprostim.qr.video_audit import do_audit_file

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    mock_vi = MagicMock(duration_sec=60.0, size_mb=100.0, rate_mbpm=200.0)
    mock_vti = MagicMock(
        start_time=datetime(2025, 1, 1, 10, 0, 0),
        end_time=datetime(2025, 1, 1, 10, 1, 0),
    )
    mock_ps = MagicMock(
        video_duration=60.0,
        video_frame_width=1920,
        video_frame_height=1080,
        video_frame_rate=30.0,
    )
    mock_ai = MagicMock(
        sample_rate=44100,
        channels=2,
        codec="pcm_s16le",
        bits_per_sample=16,
        duration_sec=60.0,
    )
    sb = {"frameRate": "30.0", "cx": 1920, "cy": 1080}
    with patch("reprostim.qr.video_audit.find_metadata_json", return_value=sb), patch(
        "reprostim.qr.video_audit.do_info_file", return_value=(mock_vi, mock_vti)
    ), patch("reprostim.qr.video_audit.do_parse", return_value=iter([mock_ps])), patch(
        "reprostim.qr.video_audit.get_audio_info_ffprobe", return_value=mock_ai
    ):
        records = list(do_audit_file(_ctx(), str(mkv)))
    assert len(records) == 1
    vr = records[0]
    assert vr.present is True
    assert vr.name == "test.mkv"
    assert vr.video_res_detected == "1920x1080"
    assert vr.duration == "60.0"
    assert vr.updated_on != "n/a"


# ===========================================================================
# do_audit_dir / do_audit_internal
# ===========================================================================


def test_do_audit_dir_yields_mkv_files(tmp_path):
    from reprostim.qr.video_audit import do_audit_dir

    (tmp_path / "a.mkv").touch()
    (tmp_path / "b.txt").touch()
    mock_rec = VaRecord(name="a.mkv", path=str(tmp_path / "a.mkv"), present=True)
    with patch("reprostim.qr.video_audit.do_audit_file", return_value=iter([mock_rec])):
        records = list(do_audit_dir(_ctx(), str(tmp_path)))
    assert len(records) == 1 and records[0].name == "a.mkv"


def test_do_audit_internal_skips_rerun_for_na():
    from reprostim.qr.video_audit import do_audit_internal

    assert list(do_audit_internal(_ctx(mode=VaMode.RERUN_FOR_NA), [])) == []


def test_do_audit_internal_skips_reset_to_na():
    from reprostim.qr.video_audit import do_audit_internal

    assert list(do_audit_internal(_ctx(mode=VaMode.RESET_TO_NA), [])) == []


def test_do_audit_internal_skips_wrong_source():
    from reprostim.qr.video_audit import do_audit_internal

    assert list(do_audit_internal(_ctx(source={VaSource.QR}), [])) == []


# ===========================================================================
# run_ext_nosignal — early-exit paths
# ===========================================================================


def test_run_ext_nosignal_wrong_source():
    from reprostim.qr.video_audit import run_ext_nosignal

    vr = _rec()
    assert run_ext_nosignal(_ctx(source={VaSource.QR}), vr) is vr


def test_run_ext_nosignal_reset_to_na_resets_value():
    from reprostim.qr.video_audit import run_ext_nosignal

    vr = _rec(no_signal_frames="5.0")
    result = run_ext_nosignal(
        _ctx(source={VaSource.NOSIGNAL}, mode=VaMode.RESET_TO_NA), vr
    )
    assert result.no_signal_frames == "n/a"


def test_run_ext_nosignal_reset_to_na_already_na():
    from reprostim.qr.video_audit import run_ext_nosignal

    ctx = _ctx(source={VaSource.NOSIGNAL}, mode=VaMode.RESET_TO_NA)
    run_ext_nosignal(ctx, _rec(no_signal_frames="n/a"))
    assert ctx.c_nosignal == 0


def test_run_ext_nosignal_rerun_for_na_skips_non_na():
    from reprostim.qr.video_audit import run_ext_nosignal

    vr = _rec(no_signal_frames="3.0")
    result = run_ext_nosignal(
        _ctx(source={VaSource.NOSIGNAL}, mode=VaMode.RERUN_FOR_NA), vr
    )
    assert result.no_signal_frames == "3.0"


# ===========================================================================
# run_ext_qr — early-exit paths
# ===========================================================================


def test_run_ext_qr_wrong_source():
    from reprostim.qr.video_audit import run_ext_qr

    vr = _rec()
    assert run_ext_qr(_ctx(source={VaSource.NOSIGNAL}), vr) is vr


def test_run_ext_qr_reset_to_na_resets_value():
    from reprostim.qr.video_audit import run_ext_qr

    vr = _rec(qr_records_number="10")
    result = run_ext_qr(_ctx(source={VaSource.QR}, mode=VaMode.RESET_TO_NA), vr)
    assert result.qr_records_number == "n/a"


def test_run_ext_qr_reset_to_na_already_na():
    from reprostim.qr.video_audit import run_ext_qr

    ctx = _ctx(source={VaSource.QR}, mode=VaMode.RESET_TO_NA)
    run_ext_qr(ctx, _rec(qr_records_number="n/a"))
    assert ctx.c_qr == 0


def test_run_ext_qr_rerun_for_na_skips_non_na():
    from reprostim.qr.video_audit import run_ext_qr

    vr = _rec(qr_records_number="5")
    result = run_ext_qr(_ctx(source={VaSource.QR}, mode=VaMode.RERUN_FOR_NA), vr)
    assert result.qr_records_number == "5"


# ===========================================================================
# do_main
# ===========================================================================


def test_do_main_invalid_path(tmp_path):
    from reprostim.qr.video_audit import do_main

    with patch.dict(os.environ, _ENV):
        assert do_main([str(tmp_path / "missing")], str(tmp_path / "out.tsv")) == 1


def test_do_main_incremental_creates_tsv(tmp_path):
    from reprostim.qr.video_audit import do_main

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    tsv = str(tmp_path / "videos.tsv")
    mock_rec = _rec(name="test.mkv", path=str(mkv))
    with patch.dict(os.environ, _ENV), patch(
        "reprostim.qr.video_audit.check_ffprobe", return_value=True
    ), patch("reprostim.qr.video_audit.do_audit", return_value=iter([mock_rec])):
        assert do_main([str(tmp_path)], tsv) == 0
    assert os.path.exists(tsv)


def test_do_main_full_mode(tmp_path):
    from reprostim.qr.video_audit import do_main

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    tsv = str(tmp_path / "videos.tsv")
    mock_rec = _rec(name="test.mkv", path=str(mkv))
    with patch.dict(os.environ, _ENV), patch(
        "reprostim.qr.video_audit.check_ffprobe", return_value=True
    ), patch("reprostim.qr.video_audit.do_audit", return_value=iter([mock_rec])):
        assert do_main([str(tmp_path)], tsv, mode=VaMode.FULL) == 0


def test_do_main_rerun_for_na_calls_do_ext(tmp_path):
    from reprostim.qr.video_audit import do_main

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    tsv = str(tmp_path / "videos.tsv")
    _save_tsv([_rec(name="test.mkv", path=str(mkv))], tsv)
    mock_rec = _rec(name="test.mkv", path=str(mkv))
    with patch.dict(os.environ, _ENV), patch(
        "reprostim.qr.video_audit.check_ffprobe", return_value=True
    ), patch(
        "reprostim.qr.video_audit.do_ext", return_value=iter([mock_rec])
    ) as mock_ext:
        assert do_main([str(tmp_path)], tsv, mode=VaMode.RERUN_FOR_NA) == 0
    mock_ext.assert_called_once()


def test_do_main_nosignal_opts_shlex_parsed(tmp_path):
    from reprostim.qr.video_audit import do_main

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    tsv = str(tmp_path / "videos.tsv")
    captured = {}

    def _capture(ctx, paths):
        captured["nosignal_opts"] = ctx.nosignal_opts
        return iter([])

    with patch.dict(os.environ, _ENV), patch(
        "reprostim.qr.video_audit.check_ffprobe", return_value=True
    ), patch("reprostim.qr.video_audit.do_audit", side_effect=_capture):
        do_main([str(tmp_path)], tsv, nosignal_opts="--number-of-checks 50")
    assert captured["nosignal_opts"] == ["--number-of-checks", "50"]


# ===========================================================================
# get_file_video_audit
# ===========================================================================


def test_get_file_video_audit_tsv_hit(tmp_path):
    from reprostim.qr.video_audit import _tsv_cache, get_file_video_audit

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    tsv = str(tmp_path / "videos.tsv")
    _save_tsv([_rec(name="test.mkv", path=str(mkv))], tsv)
    _tsv_cache.pop(tsv, None)
    result = get_file_video_audit(str(mkv), path_tsv=tsv, use_lock=False)
    assert result is not None and result.name == "test.mkv"


def test_get_file_video_audit_tsv_miss_fallback(tmp_path):
    from reprostim.qr.video_audit import _tsv_cache, get_file_video_audit

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    tsv = str(tmp_path / "videos.tsv")
    _save_tsv([_rec(name="other.mkv", path="/data/other.mkv")], tsv)
    _tsv_cache.pop(tsv, None)
    fallback = _rec(name="test.mkv", path=str(mkv))
    with patch.dict(os.environ, _ENV), patch(
        "reprostim.qr.video_audit.do_audit_file", return_value=iter([fallback])
    ):
        result = get_file_video_audit(str(mkv), path_tsv=tsv, use_lock=False)
    assert result is not None and result.name == "test.mkv"


# ===========================================================================
# iter_metadata_json — invalid JSON branch
# ===========================================================================


def test_iter_metadata_json_invalid_json(tmp_path):
    """Invalid JSON embedded in a metadata marker line is silently skipped."""
    log = tmp_path / "bad.log"
    log.write_text(
        "PREFIX REPROSTIM-METADATA-JSON: not-valid-json :REPROSTIM-METADATA-JSON\n"
    )
    assert list(iter_metadata_json(str(log))) == []


# ===========================================================================
# get_audio_info_ffprobe
# ===========================================================================


def test_get_audio_info_ffprobe_success():

    from reprostim.qr.video_audit import get_audio_info_ffprobe

    ffprobe_output = json.dumps(
        {
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "pcm_s16le",
                    "sample_rate": "44100",
                    "channels": 2,
                    "bits_per_sample": 16,
                    "tags": {"DURATION": "00:01:00.000000000"},
                }
            ]
        }
    )
    mock_result = MagicMock(stdout=ffprobe_output, returncode=0)
    with patch("reprostim.qr.video_audit.subprocess.run", return_value=mock_result):
        ai = get_audio_info_ffprobe("/fake/test.mkv")
    assert ai.codec == "pcm_s16le"
    assert ai.sample_rate == 44100
    assert ai.channels == 2
    assert ai.bits_per_sample == 16
    assert abs(ai.duration_sec - 60.0) < 0.01


def test_get_audio_info_ffprobe_duration_from_stream():
    from reprostim.qr.video_audit import get_audio_info_ffprobe

    ffprobe_output = json.dumps(
        {
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "48000",
                    "channels": 1,
                    "duration": "30.5",
                }
            ]
        }
    )
    mock_result = MagicMock(stdout=ffprobe_output, returncode=0)
    with patch("reprostim.qr.video_audit.subprocess.run", return_value=mock_result):
        ai = get_audio_info_ffprobe("/fake/test.mkv")
    assert abs(ai.duration_sec - 30.5) < 0.01


def test_get_audio_info_ffprobe_no_audio_streams():
    from reprostim.qr.video_audit import get_audio_info_ffprobe

    ffprobe_output = json.dumps({"streams": [{"codec_type": "video"}]})
    mock_result = MagicMock(stdout=ffprobe_output, returncode=0)
    with patch("reprostim.qr.video_audit.subprocess.run", return_value=mock_result):
        ai = get_audio_info_ffprobe("/fake/test.mkv")
    assert ai.codec is None


def test_get_audio_info_ffprobe_not_found():
    from reprostim.qr.video_audit import get_audio_info_ffprobe

    with patch(
        "reprostim.qr.video_audit.subprocess.run", side_effect=FileNotFoundError
    ):
        ai = get_audio_info_ffprobe("/fake/test.mkv")
    assert ai.codec is None


def test_get_audio_info_ffprobe_called_process_error():
    import subprocess as _subprocess

    from reprostim.qr.video_audit import get_audio_info_ffprobe

    err = _subprocess.CalledProcessError(1, "ffprobe", output="", stderr="error")
    with patch("reprostim.qr.video_audit.subprocess.run", side_effect=err):
        ai = get_audio_info_ffprobe("/fake/test.mkv")
    assert ai.codec is None


# ===========================================================================
# _merge_rec — name mismatch raises ValueError
# ===========================================================================


def test_merge_rec_name_mismatch_raises():
    with pytest.raises(ValueError, match="Record names do not match"):
        _merge_rec(_ctx(), _rec(name="a.mkv"), _rec(name="b.mkv"))


# ===========================================================================
# _merge_recs — additional branches
# ===========================================================================


def test_merge_recs_force_empty_recs_cur():
    """FORCE mode with empty recs_cur returns recs_new directly."""
    r_old = _rec(name="a.mkv", updated_on=_TS_EARLY)
    r_new = _rec(name="b.mkv", updated_on=_TS_EARLY)
    result = _merge_recs(_ctx(mode=VaMode.FORCE), [r_old], [], [r_new])
    assert result == [r_new]


def test_merge_recs_incremental_new_record_added():
    """Incremental mode: a brand-new record is added alongside existing ones."""
    r_old = _rec(name="existing.mkv", updated_on="n/a")
    r_cur = _rec(name="existing.mkv", updated_on=_TS_EARLY)
    r_new = _rec(name="brand_new.mkv", updated_on=_TS_EARLY)
    result = _merge_recs(_ctx(mode=VaMode.INCREMENTAL), [r_old], [r_cur], [r_new])
    names = {r.name for r in result}
    assert "brand_new.mkv" in names and "existing.mkv" in names


# ===========================================================================
# do_audit_dir — additional branches
# ===========================================================================


def test_do_audit_dir_missing_path(tmp_path):
    from reprostim.qr.video_audit import do_audit_dir

    assert list(do_audit_dir(_ctx(), str(tmp_path / "missing"))) == []


def test_do_audit_dir_not_a_directory(tmp_path):
    from reprostim.qr.video_audit import do_audit_dir

    f = tmp_path / "file.txt"
    f.touch()
    assert list(do_audit_dir(_ctx(), str(f))) == []


def test_do_audit_dir_max_counter(tmp_path):
    from reprostim.qr.video_audit import do_audit_dir

    assert list(do_audit_dir(_ctx(max_counter=0, c_internal=0), str(tmp_path))) == []


def test_do_audit_dir_recursive(tmp_path):
    from reprostim.qr.video_audit import do_audit_dir

    subdir = tmp_path / "sub"
    subdir.mkdir()
    (subdir / "a.mkv").touch()
    mock_rec = VaRecord(name="a.mkv", path=str(subdir / "a.mkv"), present=True)
    with patch("reprostim.qr.video_audit.do_audit_file", return_value=iter([mock_rec])):
        records = list(do_audit_dir(_ctx(recursive=True), str(tmp_path)))
    assert len(records) == 1 and records[0].name == "a.mkv"


# ===========================================================================
# do_audit_file — skip by base name (after existence check, line 734-736)
# ===========================================================================


def test_do_audit_file_skip_by_base_name(tmp_path):
    from reprostim.qr.video_audit import do_audit_file

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    ctx = _ctx(skip_names={"test.mkv"})
    assert list(do_audit_file(ctx, str(mkv))) == []


# ===========================================================================
# do_audit_internal — file and directory paths
# ===========================================================================


def test_do_audit_internal_with_file(tmp_path):
    from reprostim.qr.video_audit import do_audit_internal

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    mock_rec = VaRecord(name="test.mkv", path=str(mkv), present=True)
    with patch("reprostim.qr.video_audit.do_audit_file", return_value=iter([mock_rec])):
        records = list(do_audit_internal(_ctx(), [str(mkv)]))
    assert len(records) == 1


def test_do_audit_internal_with_dir(tmp_path):
    from reprostim.qr.video_audit import do_audit_internal

    mock_rec = VaRecord(name="a.mkv", path=str(tmp_path / "a.mkv"), present=True)
    with patch("reprostim.qr.video_audit.do_audit_dir", return_value=iter([mock_rec])):
        records = list(do_audit_internal(_ctx(), [str(tmp_path)]))
    assert len(records) == 1


def test_do_audit_internal_nonexistent_path(tmp_path):
    from reprostim.qr.video_audit import do_audit_internal

    records = list(do_audit_internal(_ctx(), [str(tmp_path / "missing")]))
    assert records == []


# ===========================================================================
# run_ext_nosignal — max_counter / path_mask early exits
# ===========================================================================


def test_run_ext_nosignal_max_counter():
    from reprostim.qr.video_audit import run_ext_nosignal

    vr = _rec(no_signal_frames="n/a")
    ctx = _ctx(source={VaSource.NOSIGNAL}, max_counter=0, c_nosignal=0)
    assert run_ext_nosignal(ctx, vr) is vr


def test_run_ext_nosignal_path_mask_no_match():
    from reprostim.qr.video_audit import run_ext_nosignal

    vr = _rec(no_signal_frames="n/a", path="/data/2024/video.mkv")
    ctx = _ctx(source={VaSource.NOSIGNAL}, path_mask="*/2025/*")
    assert run_ext_nosignal(ctx, vr) is vr


# ===========================================================================
# run_ext_nosignal — subprocess execution
# ===========================================================================


def test_run_ext_nosignal_subprocess_success(tmp_path):
    from reprostim.qr.video_audit import run_ext_nosignal

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    vr = _rec(name="test.mkv", path=str(mkv), no_signal_frames="n/a", start_date="n/a")
    ctx = _ctx(
        source={VaSource.NOSIGNAL},
        nosignal_data_dir=str(tmp_path / "data"),
        nosignal_log_dir=str(tmp_path / "log"),
    )

    def _fake_run(cmd, **kwargs):
        for i, arg in enumerate(cmd):
            if arg == "--output" and i + 1 < len(cmd):
                out = cmd[i + 1]
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "w") as f:
                    json.dump({"nosignal_rate": 0.05}, f)
        return MagicMock(returncode=0)

    with patch("reprostim.qr.video_audit.subprocess.run", side_effect=_fake_run):
        result = run_ext_nosignal(ctx, vr)
    assert result.no_signal_frames == "5.0"


def test_run_ext_nosignal_no_nosignal_rate_key(tmp_path):
    """JSON output without 'nosignal_rate' sets no_signal_frames to '0.0'."""
    from reprostim.qr.video_audit import run_ext_nosignal

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    vr = _rec(name="test.mkv", path=str(mkv), no_signal_frames="n/a", start_date="n/a")
    ctx = _ctx(
        source={VaSource.NOSIGNAL},
        nosignal_data_dir=str(tmp_path / "data"),
        nosignal_log_dir=str(tmp_path / "log"),
    )

    def _fake_run(cmd, **kwargs):
        for i, arg in enumerate(cmd):
            if arg == "--output" and i + 1 < len(cmd):
                out = cmd[i + 1]
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "w") as f:
                    json.dump({"other_key": 42}, f)
        return MagicMock(returncode=0)

    with patch("reprostim.qr.video_audit.subprocess.run", side_effect=_fake_run):
        result = run_ext_nosignal(ctx, vr)
    assert result.no_signal_frames == "0.0"


def test_run_ext_nosignal_subprocess_error(tmp_path):
    """CalledProcessError from detect-noscreen → no_signal_frames unchanged."""
    import subprocess as _subprocess

    from reprostim.qr.video_audit import run_ext_nosignal

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    vr = _rec(name="test.mkv", path=str(mkv), no_signal_frames="n/a", start_date="n/a")
    ctx = _ctx(
        source={VaSource.NOSIGNAL},
        nosignal_data_dir=str(tmp_path / "data"),
        nosignal_log_dir=str(tmp_path / "log"),
    )
    err = _subprocess.CalledProcessError(1, "reprostim", output="", stderr="")
    with patch("reprostim.qr.video_audit.subprocess.run", side_effect=err):
        result = run_ext_nosignal(ctx, vr)
    assert result.no_signal_frames == "n/a"


# ===========================================================================
# run_ext_qr — max_counter / path_mask early exits
# ===========================================================================


def test_run_ext_qr_max_counter():
    from reprostim.qr.video_audit import run_ext_qr

    vr = _rec(qr_records_number="n/a")
    ctx = _ctx(source={VaSource.QR}, max_counter=0, c_qr=0)
    assert run_ext_qr(ctx, vr) is vr


def test_run_ext_qr_path_mask_no_match():
    from reprostim.qr.video_audit import run_ext_qr

    vr = _rec(qr_records_number="n/a", path="/data/2024/video.mkv")
    ctx = _ctx(source={VaSource.QR}, path_mask="*/2025/*")
    assert run_ext_qr(ctx, vr) is vr


# ===========================================================================
# run_ext_qr — subprocess execution
# ===========================================================================


def test_run_ext_qr_subprocess_success(tmp_path):
    from reprostim.qr.video_audit import run_ext_qr

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    vr = _rec(name="test.mkv", path=str(mkv), qr_records_number="n/a", start_date="n/a")
    ctx = _ctx(
        source={VaSource.QR},
        qr_data_dir=str(tmp_path / "qr_data"),
        qr_log_dir=str(tmp_path / "qr_log"),
    )
    summary_line = '{"type": "ParseSummary", "qr_count": 42}\n'

    def _fake_run(cmd, **kwargs):
        stdout = kwargs.get("stdout")
        if stdout is not None and "qr-parse" in cmd:
            stdout.write(summary_line)
        return MagicMock(returncode=0)

    with patch("reprostim.qr.video_audit.subprocess.run", side_effect=_fake_run):
        result = run_ext_qr(ctx, vr)
    assert result.qr_records_number == "42"


def test_run_ext_qr_subprocess_ffmpeg_error(tmp_path):
    """ffmpeg CalledProcessError → qr_records_number stays at '-2'."""
    import subprocess as _subprocess

    from reprostim.qr.video_audit import run_ext_qr

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    vr = _rec(name="test.mkv", path=str(mkv), qr_records_number="n/a", start_date="n/a")
    ctx = _ctx(
        source={VaSource.QR},
        qr_data_dir=str(tmp_path / "qr_data"),
        qr_log_dir=str(tmp_path / "qr_log"),
    )
    err = _subprocess.CalledProcessError(1, "ffmpeg", output="", stderr="")
    with patch("reprostim.qr.video_audit.subprocess.run", side_effect=err):
        result = run_ext_qr(ctx, vr)
    assert result.qr_records_number == "-2"


def test_run_ext_qr_no_parse_summary(tmp_path):
    """qr-parse writes nothing → qr_records_number stays at '-1'."""
    from reprostim.qr.video_audit import run_ext_qr

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    vr = _rec(name="test.mkv", path=str(mkv), qr_records_number="n/a", start_date="n/a")
    ctx = _ctx(
        source={VaSource.QR},
        qr_data_dir=str(tmp_path / "qr_data"),
        qr_log_dir=str(tmp_path / "qr_log"),
    )

    def _fake_run(cmd, **kwargs):
        return MagicMock(returncode=0)

    with patch("reprostim.qr.video_audit.subprocess.run", side_effect=_fake_run):
        result = run_ext_qr(ctx, vr)
    assert result.qr_records_number == "-1"


# ===========================================================================
# run_ext_all / do_audit
# ===========================================================================


def test_run_ext_all_with_internal_source():
    from reprostim.qr.video_audit import run_ext_all

    vr = _rec()
    ctx = _ctx(source={VaSource.INTERNAL})
    assert run_ext_all(ctx, vr) is vr


def test_do_audit_delegates(tmp_path):
    from reprostim.qr.video_audit import do_audit

    mkv = tmp_path / "a.mkv"
    mkv.touch()
    mock_rec = VaRecord(name="a.mkv", path=str(mkv), present=True)
    with patch(
        "reprostim.qr.video_audit.do_audit_internal", return_value=iter([mock_rec])
    ), patch("reprostim.qr.video_audit.run_ext_all", return_value=mock_rec):
        records = list(do_audit(_ctx(), [str(tmp_path)]))
    assert len(records) == 1


# ===========================================================================
# do_ext
# ===========================================================================


def test_do_ext_no_filter_processes_all():
    """Empty path list → no filter; all records passed to run_ext_all."""
    from reprostim.qr.video_audit import do_ext

    vr = _rec(name="a.mkv", path="/data/a.mkv")
    ctx = _ctx(source={VaSource.INTERNAL})
    with patch("reprostim.qr.video_audit.run_ext_all", return_value=vr) as mock_ext:
        list(do_ext(ctx, [vr], []))
    mock_ext.assert_called_once()


def test_do_ext_wildcard_processes_all():
    """Path list ['*'] disables the filter; all records are processed."""
    from reprostim.qr.video_audit import do_ext

    vr = _rec(name="a.mkv", path="/data/a.mkv")
    ctx = _ctx(source={VaSource.INTERNAL})
    with patch("reprostim.qr.video_audit.run_ext_all", return_value=vr) as mock_ext:
        list(do_ext(ctx, [vr], ["*"]))
    mock_ext.assert_called_once()


def test_do_ext_filter_by_file(tmp_path):
    """Record path matches an explicit file path in the filter."""
    from reprostim.qr.video_audit import do_ext

    mkv = tmp_path / "a.mkv"
    mkv.touch()
    vr = _rec(name="a.mkv", path=str(mkv))
    ctx = _ctx(source={VaSource.INTERNAL})
    with patch("reprostim.qr.video_audit.run_ext_all", return_value=vr) as mock_ext:
        list(do_ext(ctx, [vr], [str(mkv)]))
    mock_ext.assert_called_once()


def test_do_ext_filter_by_directory(tmp_path):
    """Record path starts with a directory in the filter."""
    from reprostim.qr.video_audit import do_ext

    mkv = tmp_path / "a.mkv"
    mkv.touch()
    vr = _rec(name="a.mkv", path=str(mkv))
    ctx = _ctx(source={VaSource.INTERNAL})
    with patch("reprostim.qr.video_audit.run_ext_all", return_value=vr) as mock_ext:
        list(do_ext(ctx, [vr], [str(tmp_path)]))
    mock_ext.assert_called_once()


def test_do_ext_no_filter_match_yields_unchanged(tmp_path):
    """Record not matching any filter path is yielded unchanged without processing."""
    from reprostim.qr.video_audit import do_ext

    other = tmp_path / "other"
    other.mkdir()
    vr = _rec(name="a.mkv", path="/data/a.mkv")
    ctx = _ctx(source={VaSource.INTERNAL})
    with patch("reprostim.qr.video_audit.run_ext_all") as mock_ext:
        result = list(do_ext(ctx, [vr], [str(other)]))
    mock_ext.assert_not_called()
    assert result == [vr]


# ===========================================================================
# get_file_video_audit — Timeout and generic exception fallbacks
# ===========================================================================


def test_get_file_video_audit_timeout_falls_back(tmp_path):
    from filelock import Timeout

    from reprostim.qr.video_audit import _tsv_cache, get_file_video_audit

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    tsv = str(tmp_path / "videos.tsv")
    _save_tsv([_rec(name="test.mkv", path=str(mkv))], tsv)
    _tsv_cache.pop(tsv, None)
    fallback = _rec(name="test.mkv", path=str(mkv))
    with patch(
        "reprostim.qr.video_audit._get_tsv_records", side_effect=Timeout(tsv)
    ), patch.dict(os.environ, _ENV), patch(
        "reprostim.qr.video_audit.do_audit_file", return_value=iter([fallback])
    ):
        result = get_file_video_audit(str(mkv), path_tsv=tsv, use_lock=False)
    assert result is not None and result.name == "test.mkv"


def test_get_file_video_audit_exception_falls_back(tmp_path):
    from reprostim.qr.video_audit import _tsv_cache, get_file_video_audit

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    tsv = str(tmp_path / "videos.tsv")
    _save_tsv([_rec(name="test.mkv", path=str(mkv))], tsv)
    _tsv_cache.pop(tsv, None)
    fallback = _rec(name="test.mkv", path=str(mkv))
    with patch(
        "reprostim.qr.video_audit._get_tsv_records", side_effect=IOError("disk error")
    ), patch.dict(os.environ, _ENV), patch(
        "reprostim.qr.video_audit.do_audit_file", return_value=iter([fallback])
    ):
        result = get_file_video_audit(str(mkv), path_tsv=tsv, use_lock=False)
    assert result is not None and result.name == "test.mkv"


# ===========================================================================
# _parse_rec_datetime — ValueError path
# ===========================================================================


def test_parse_rec_datetime_invalid_format():
    """Malformed strings return None rather than raising ValueError."""
    assert _parse_rec_datetime("not-a-date", "not-a-time") is None


# ===========================================================================
# find_video_audit_by_timerange — skip conditions
# ===========================================================================


def test_find_video_audit_skip_not_present(tmp_path):
    """Records with present=False are excluded from results."""
    r = VaRecord(
        name="a.mkv",
        path="/data/a.mkv",
        present=False,
        complete=True,
        start_date="2025-01-01",
        start_time="10:00:00.000",
        end_date="2025-01-01",
        end_time="11:00:00.000",
    )
    path = _tsv_with(tmp_path, [r])
    result = find_video_audit_by_timerange(
        path,
        datetime(2025, 1, 1, 9, 0),
        datetime(2025, 1, 1, 12, 0),
        use_lock=False,
    )
    assert result == []


def test_find_video_audit_skip_not_complete(tmp_path):
    """Records with complete=False are excluded from results."""
    r = VaRecord(
        name="a.mkv",
        path="/data/a.mkv",
        present=True,
        complete=False,
        start_date="2025-01-01",
        start_time="10:00:00.000",
        end_date="2025-01-01",
        end_time="11:00:00.000",
    )
    path = _tsv_with(tmp_path, [r])
    result = find_video_audit_by_timerange(
        path,
        datetime(2025, 1, 1, 9, 0),
        datetime(2025, 1, 1, 12, 0),
        use_lock=False,
    )
    assert result == []


def test_find_video_audit_skip_na_start(tmp_path):
    """Records with n/a start_date are excluded."""
    r = VaRecord(
        name="a.mkv",
        path="/data/a.mkv",
        present=True,
        complete=True,
        start_date="n/a",
        start_time="10:00:00.000",
        end_date="2025-01-01",
        end_time="11:00:00.000",
    )
    path = _tsv_with(tmp_path, [r])
    result = find_video_audit_by_timerange(
        path,
        datetime(2025, 1, 1, 9, 0),
        datetime(2025, 1, 1, 12, 0),
        use_lock=False,
    )
    assert result == []


def test_find_video_audit_skip_na_end(tmp_path):
    """Records with n/a end_date are excluded (end is required for intersection)."""
    r = VaRecord(
        name="a.mkv",
        path="/data/a.mkv",
        present=True,
        complete=True,
        start_date="2025-01-01",
        start_time="10:00:00.000",
        end_date="n/a",
        end_time="n/a",
    )
    path = _tsv_with(tmp_path, [r])
    result = find_video_audit_by_timerange(
        path,
        datetime(2025, 1, 1, 9, 0),
        datetime(2025, 1, 1, 12, 0),
        use_lock=False,
    )
    assert result == []


# ===========================================================================
# do_main — additional branches
# ===========================================================================


def test_do_main_ffprobe_missing_still_returns_zero(tmp_path):
    """When ffprobe is absent do_main emits an error message but returns 0."""
    from reprostim.qr.video_audit import do_main

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    tsv = str(tmp_path / "videos.tsv")
    mock_rec = _rec(name="test.mkv", path=str(mkv))
    messages = []
    with patch.dict(os.environ, _ENV), patch(
        "reprostim.qr.video_audit.check_ffprobe", return_value=False
    ), patch("reprostim.qr.video_audit.do_audit", return_value=iter([mock_rec])):
        rc = do_main([str(tmp_path)], tsv, out_func=messages.append)
    assert rc == 0
    assert any("ffprobe" in m for m in messages)


def test_do_main_verbose_prints_json(tmp_path):
    """verbose=True causes each record to be printed as JSON via out_func."""
    from reprostim.qr.video_audit import do_main

    mkv = tmp_path / "test.mkv"
    mkv.touch()
    tsv = str(tmp_path / "videos.tsv")
    mock_rec = _rec(name="test.mkv", path=str(mkv))
    outputs = []
    with patch.dict(os.environ, _ENV), patch(
        "reprostim.qr.video_audit.check_ffprobe", return_value=True
    ), patch("reprostim.qr.video_audit.do_audit", return_value=iter([mock_rec])):
        do_main([str(tmp_path)], tsv, verbose=True, out_func=outputs.append)
    assert len(outputs) >= 1


def test_do_main_incremental_merges_existing(tmp_path):
    """Incremental mode loads an existing TSV and merges new records into it."""
    from reprostim.qr.video_audit import _load_tsv, do_main

    mkv = tmp_path / "new.mkv"
    mkv.touch()
    tsv = str(tmp_path / "videos.tsv")
    existing = _rec(name="old.mkv", path=str(tmp_path / "old.mkv"))
    _save_tsv([existing], tsv)
    new_rec = _rec(name="new.mkv", path=str(mkv))
    with patch.dict(os.environ, _ENV), patch(
        "reprostim.qr.video_audit.check_ffprobe", return_value=True
    ), patch("reprostim.qr.video_audit.do_audit", return_value=iter([new_rec])):
        rc = do_main([str(tmp_path)], tsv, mode=VaMode.INCREMENTAL)
    assert rc == 0
    names = {r.name for r in _load_tsv(tsv)}
    assert "old.mkv" in names and "new.mkv" in names
