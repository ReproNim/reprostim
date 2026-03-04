# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for the Datetime / Timezone public API in reprostim.qr.bids_inject."""

import re
from datetime import datetime, time, timezone
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytest

from reprostim.qr.bids_inject import (
    MediaSuffix,
    ScanMetadata,
    ScanRecord,
    _calc_bids_output_stem,
    _calc_media_suffix,
    _calc_scan_duration_sec,
    _calc_scan_start_end_ts,
    _find_bids_root,
    _is_scans_file,
    do_main,
    dt_bids_to_reprostim,
    dt_bids_to_utc,
    dt_convert,
    dt_parse_bids,
    dt_parse_dicom_time,
    dt_reprostim_to_bids,
    dt_reprostim_to_utc,
    dt_resolve_tz,
    dt_time_to_sec,
    dt_tz_label,
    dt_utc_to_bids,
    dt_utc_to_reprostim,
)

# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

UTC = timezone.utc
NY = ZoneInfo("America/New_York")  # UTC-5 (winter) / UTC-4 (summer)
BERLIN = ZoneInfo("Europe/Berlin")  # UTC+1 (winter) / UTC+2 (summer)

# A fixed naive datetime in winter so UTC offset is deterministic (-5 for NY)
_WINTER_NAIVE = datetime(2025, 1, 15, 12, 0, 0)  # 2025-01-15 12:00:00
_SUMMER_NAIVE = datetime(2025, 8, 14, 15, 6, 9, 742500)  # 2025-08-14 (DST)


# ===========================================================================
# dt_resolve_tz
# ===========================================================================


def test_dt_resolve_tz_local_returns_tzinfo():
    tz = dt_resolve_tz("local")
    assert tz is not None
    # Must be a valid tzinfo: attaching it to a datetime should work
    aware = datetime.now(tz)
    assert aware.utcoffset() is not None


def test_dt_resolve_tz_local_case_insensitive():
    assert dt_resolve_tz("LOCAL") is not None
    assert dt_resolve_tz("Local") is not None


def test_dt_resolve_tz_utc():
    tz = dt_resolve_tz("UTC")
    assert isinstance(tz, ZoneInfo)
    offset = datetime(2025, 1, 1, tzinfo=tz).utcoffset().total_seconds()
    assert offset == 0.0


def test_dt_resolve_tz_iana_new_york():
    tz = dt_resolve_tz("America/New_York")
    assert isinstance(tz, ZoneInfo)


def test_dt_resolve_tz_iana_berlin():
    tz = dt_resolve_tz("Europe/Berlin")
    assert isinstance(tz, ZoneInfo)


def test_dt_resolve_tz_invalid_raises():
    with pytest.raises(ZoneInfoNotFoundError):
        dt_resolve_tz("Invalid/NotAZone")


def test_dt_resolve_tz_cached():
    # lru_cache: same name → identical object
    tz1 = dt_resolve_tz("America/Chicago")
    tz2 = dt_resolve_tz("America/Chicago")
    assert tz1 is tz2


# ===========================================================================
# dt_tz_label
# ===========================================================================

_UTC_OFFSET_RE = re.compile(r"^UTC[+-]\d{2}:\d{2}$")


def test_dt_tz_label_format():
    label = dt_tz_label("UTC")
    assert _UTC_OFFSET_RE.match(label), f"Unexpected format: {label!r}"


def test_dt_tz_label_utc_is_zero():
    assert dt_tz_label("UTC") == "UTC+00:00"


def test_dt_tz_label_local_format():
    label = dt_tz_label("local")
    assert _UTC_OFFSET_RE.match(label), f"Unexpected format: {label!r}"


def test_dt_tz_label_known_zone():
    # America/New_York is either UTC-05:00 or UTC-04:00 depending on DST;
    # either way the format must be correct.
    label = dt_tz_label("America/New_York")
    assert label in ("UTC-05:00", "UTC-04:00"), f"Unexpected offset: {label!r}"


# ===========================================================================
# dt_parse_dicom_time
# ===========================================================================


def test_dt_parse_dicom_time_full():
    t = dt_parse_dicom_time("151953.397500")
    assert t == time(15, 19, 53, 397500)


def test_dt_parse_dicom_time_no_fraction():
    t = dt_parse_dicom_time("151953")
    assert t == time(15, 19, 53, 0)


def test_dt_parse_dicom_time_short_fraction():
    # 1-digit fraction → padded to 6 digits on the right: "5" → 500000 µs
    t = dt_parse_dicom_time("120000.5")
    assert t == time(12, 0, 0, 500000)


def test_dt_parse_dicom_time_leap_second_clamped():
    # SS=60 is clamped to 59
    t = dt_parse_dicom_time("235960")
    assert t == time(23, 59, 59, 0)


def test_dt_parse_dicom_time_whitespace_stripped():
    t = dt_parse_dicom_time("  120000  ")
    assert t == time(12, 0, 0, 0)


def test_dt_parse_dicom_time_invalid_raises():
    with pytest.raises(ValueError):
        dt_parse_dicom_time("not-a-time")


def test_dt_parse_dicom_time_invalid_short_raises():
    with pytest.raises(ValueError):
        dt_parse_dicom_time("1234")


# ===========================================================================
# dt_time_to_sec
# ===========================================================================


def test_dt_time_to_sec_midnight():
    assert dt_time_to_sec(time(0, 0, 0)) == 0.0


def test_dt_time_to_sec_one_hour():
    assert dt_time_to_sec(time(1, 0, 0)) == 3600.0


def test_dt_time_to_sec_known_value():
    # 15:19:53.397500
    expected = 15 * 3600 + 19 * 60 + 53 + 397500 / 1_000_000
    assert dt_time_to_sec(time(15, 19, 53, 397500)) == pytest.approx(expected)


def test_dt_time_to_sec_microseconds():
    t = time(0, 0, 0, 1)
    assert dt_time_to_sec(t) == pytest.approx(1e-6)


# ===========================================================================
# dt_parse_bids
# ===========================================================================


def test_dt_parse_bids_naive():
    s = "2025-08-14T15:06:09.742500"
    dt = dt_parse_bids(s)
    assert dt == datetime(2025, 8, 14, 15, 6, 9, 742500)
    assert dt.tzinfo is None


def test_dt_parse_bids_strips_utc_offset():
    # String carries +00:00 but result must be naive
    s = "2025-08-14T20:06:09.742500+00:00"
    dt = dt_parse_bids(s)
    assert dt.tzinfo is None
    assert dt == datetime(2025, 8, 14, 20, 6, 9, 742500)


def test_dt_parse_bids_invalid_raises():
    with pytest.raises(ValueError):
        dt_parse_bids("not-a-date")


# ===========================================================================
# dt_convert
# ===========================================================================


def test_dt_convert_returns_naive():
    result = dt_convert(_WINTER_NAIVE, NY, UTC)
    assert result.tzinfo is None


def test_dt_convert_ny_to_utc_winter():
    # New York in January is UTC-5; 12:00 NY → 17:00 UTC
    result = dt_convert(_WINTER_NAIVE, NY, UTC)
    assert result == datetime(2025, 1, 15, 17, 0, 0)


def test_dt_convert_utc_to_ny_winter():
    utc_dt = datetime(2025, 1, 15, 17, 0, 0)
    result = dt_convert(utc_dt, UTC, NY)
    assert result == _WINTER_NAIVE


def test_dt_convert_roundtrip():
    result = dt_convert(dt_convert(_WINTER_NAIVE, NY, UTC), UTC, NY)
    assert result == _WINTER_NAIVE


def test_dt_convert_same_timezone_identity():
    result = dt_convert(_WINTER_NAIVE, UTC, UTC)
    assert result == _WINTER_NAIVE


# ===========================================================================
# dt_reprostim_to_utc / dt_bids_to_utc
# ===========================================================================


def test_dt_reprostim_to_utc_winter():
    result = dt_reprostim_to_utc(_WINTER_NAIVE, NY)
    assert result == datetime(2025, 1, 15, 17, 0, 0)
    assert result.tzinfo is None


def test_dt_reprostim_to_utc_already_utc():
    utc_dt = datetime(2025, 1, 15, 12, 0, 0)
    result = dt_reprostim_to_utc(utc_dt, UTC)
    assert result == utc_dt


def test_dt_bids_to_utc_winter():
    # Same arithmetic as reprostim — independent function but same logic
    result = dt_bids_to_utc(_WINTER_NAIVE, NY)
    assert result == datetime(2025, 1, 15, 17, 0, 0)
    assert result.tzinfo is None


def test_dt_bids_to_utc_utc_zone():
    dt = datetime(2025, 8, 14, 19, 6, 9, 742500)
    result = dt_bids_to_utc(dt, ZoneInfo("UTC"))
    assert result == dt


# ===========================================================================
# dt_utc_to_reprostim / dt_utc_to_bids
# ===========================================================================


def test_dt_utc_to_reprostim_winter():
    utc_dt = datetime(2025, 1, 15, 17, 0, 0)
    result = dt_utc_to_reprostim(utc_dt, NY)
    assert result == _WINTER_NAIVE
    assert result.tzinfo is None


def test_dt_utc_to_bids_winter():
    utc_dt = datetime(2025, 1, 15, 17, 0, 0)
    result = dt_utc_to_bids(utc_dt, NY)
    assert result == _WINTER_NAIVE
    assert result.tzinfo is None


def test_dt_utc_to_reprostim_roundtrip():
    utc = dt_reprostim_to_utc(_SUMMER_NAIVE, NY)
    result = dt_utc_to_reprostim(utc, NY)
    assert result == _SUMMER_NAIVE


def test_dt_utc_to_bids_roundtrip():
    utc = dt_bids_to_utc(_SUMMER_NAIVE, NY)
    result = dt_utc_to_bids(utc, NY)
    assert result == _SUMMER_NAIVE


# ===========================================================================
# dt_reprostim_to_bids / dt_bids_to_reprostim
# ===========================================================================


def test_dt_reprostim_to_bids_same_tz_identity():
    result = dt_reprostim_to_bids(_WINTER_NAIVE, NY, NY)
    assert result == _WINTER_NAIVE


def test_dt_reprostim_to_bids_ny_to_utc():
    # NY winter 12:00 → UTC 17:00 expressed as naive UTC (BIDS stored in UTC)
    result = dt_reprostim_to_bids(_WINTER_NAIVE, NY, ZoneInfo("UTC"))
    assert result == datetime(2025, 1, 15, 17, 0, 0)
    assert result.tzinfo is None


def test_dt_reprostim_to_bids_ny_to_berlin_winter():
    # NY UTC-5 → UTC → Berlin UTC+1: 12:00 NY → 17:00 UTC → 18:00 Berlin
    result = dt_reprostim_to_bids(_WINTER_NAIVE, NY, BERLIN)
    assert result == datetime(2025, 1, 15, 18, 0, 0)


def test_dt_bids_to_reprostim_same_tz_identity():
    result = dt_bids_to_reprostim(_WINTER_NAIVE, NY, NY)
    assert result == _WINTER_NAIVE


def test_dt_bids_to_reprostim_utc_to_ny_winter():
    # BIDS stored as UTC 17:00 → ReproStim NY 12:00
    utc_bids = datetime(2025, 1, 15, 17, 0, 0)
    result = dt_bids_to_reprostim(utc_bids, ZoneInfo("UTC"), NY)
    assert result == _WINTER_NAIVE


def test_dt_reprostim_to_bids_roundtrip():
    converted = dt_reprostim_to_bids(_SUMMER_NAIVE, NY, BERLIN)
    restored = dt_bids_to_reprostim(converted, BERLIN, NY)
    assert restored == _SUMMER_NAIVE


# ===========================================================================
# _is_scans_file
# ===========================================================================


def test_is_scans_file_true(tmp_path):
    f = tmp_path / "sub-qa_ses-20250814_scans.tsv"
    f.write_text("filename\tacq_time\n")
    assert _is_scans_file(str(f)) is True


def test_is_scans_file_directory_false(tmp_path):
    assert _is_scans_file(str(tmp_path)) is False


def test_is_scans_file_non_matching_name_false(tmp_path):
    f = tmp_path / "something.tsv"
    f.write_text("")
    assert _is_scans_file(str(f)) is False


# ===========================================================================
# _calc_bids_output_stem
# ===========================================================================


def test_calc_bids_output_stem_standard():
    stem, reproin = _calc_bids_output_stem(
        "func/sub-qa_ses-20250814_acq-faX77_bold.nii.gz"
    )
    assert stem == "func/sub-qa_ses-20250814_acq-faX77"
    assert reproin == ""


def test_calc_bids_output_stem_reproin_dup():
    stem, reproin = _calc_bids_output_stem(
        "func/sub-qa_ses-20250814_task-rest_acq-p2_bold__dup-01.nii.gz"
    )
    assert stem == "func/sub-qa_ses-20250814_task-rest_acq-p2"
    assert reproin == "__dup-01"


def test_calc_bids_output_stem_nii_not_gz():
    stem, reproin = _calc_bids_output_stem(
        "func/sub-qa_ses-20250814_acq-faX77_bold.nii"
    )
    assert stem == "func/sub-qa_ses-20250814_acq-faX77"
    assert reproin == ""


# ===========================================================================
# _calc_media_suffix
# ===========================================================================


def test_calc_media_suffix_video_only():
    va = SimpleNamespace(video_res_detected="1920x1080", audio_sr="n/a")
    assert _calc_media_suffix(va) == MediaSuffix.VIDEO


def test_calc_media_suffix_audio_only():
    va = SimpleNamespace(video_res_detected="n/a", audio_sr="44100")
    assert _calc_media_suffix(va) == MediaSuffix.AUDIO


def test_calc_media_suffix_audiovideo():
    va = SimpleNamespace(video_res_detected="1920x1080", audio_sr="44100")
    assert _calc_media_suffix(va) == MediaSuffix.AUDIOVIDEO


def test_calc_media_suffix_neither_returns_none():
    va = SimpleNamespace(video_res_detected="n/a", audio_sr="n/a", name="test.mkv")
    assert _calc_media_suffix(va) is None


# ===========================================================================
# _calc_scan_duration_sec
# ===========================================================================


def test_calc_scan_duration_sec_priority1_frame_acquisition():
    # 500 ms → 0.5 s
    r = ScanRecord(
        filename="func/test_bold.nii.gz",
        acq_time="2025-01-15T12:00:00",
        metadata=ScanMetadata(FrameAcquisitionDuration=500.0),
    )
    assert _calc_scan_duration_sec(r) == pytest.approx(0.5)


def test_calc_scan_duration_sec_priority2_acquisition_time():
    # 3 volumes with TR=2 s: times 0, 2, 4 s → duration = (4-0)+2 = 6 s
    r = ScanRecord(
        filename="func/test_bold.nii.gz",
        acq_time="2025-01-15T12:00:00",
        metadata=ScanMetadata(AcquisitionTime=["120000", "120002", "120004"]),
    )
    assert _calc_scan_duration_sec(r) == pytest.approx(6.0)


def test_calc_scan_duration_sec_priority2_single_element_falls_through():
    # Single AcquisitionTime element → insufficient for Priority 2; falls to Priority 3
    r = ScanRecord(
        filename="func/test_bold.nii.gz",
        acq_time="2025-01-15T12:00:00",
        metadata=ScanMetadata(
            AcquisitionTime=["120000"], RepetitionTime=2.0, NumberOfVolumes=10
        ),
    )
    assert _calc_scan_duration_sec(r) == pytest.approx(20.0)


def test_calc_scan_duration_sec_priority3_tr_times_volumes():
    r = ScanRecord(
        filename="func/test_bold.nii.gz",
        acq_time="2025-01-15T12:00:00",
        metadata=ScanMetadata(RepetitionTime=2.5, NumberOfVolumes=8),
    )
    assert _calc_scan_duration_sec(r) == pytest.approx(20.0)


def test_calc_scan_duration_sec_no_metadata_returns_none():
    r = ScanRecord(filename="func/test_bold.nii.gz", acq_time="2025-01-15T12:00:00")
    assert _calc_scan_duration_sec(r) is None


# ===========================================================================
# _calc_scan_start_end_ts
# ===========================================================================


def test_calc_scan_start_end_ts_basic():
    r = ScanRecord(
        filename="func/test_bold.nii.gz",
        acq_time="2025-01-15T12:00:00",
        duration_sec=300.0,
    )
    result = _calc_scan_start_end_ts(r)
    assert result is not None
    start, end = result
    assert start == datetime(2025, 1, 15, 12, 0, 0)
    assert end == datetime(2025, 1, 15, 12, 5, 0)


def test_calc_scan_start_end_ts_time_offset():
    r = ScanRecord(
        filename="func/test_bold.nii.gz",
        acq_time="2025-01-15T12:00:00",
        duration_sec=300.0,
    )
    result = _calc_scan_start_end_ts(r, time_offset=10.0)
    assert result is not None
    start, end = result
    assert start == datetime(2025, 1, 15, 12, 0, 10)
    assert end == datetime(2025, 1, 15, 12, 5, 10)


def test_calc_scan_start_end_ts_timezone_conversion():
    # BIDS acq_time stored as UTC 17:00; ReproStim is NY (UTC-5 in January)
    # Expected: start shifted to NY 12:00
    r = ScanRecord(
        filename="func/test_bold.nii.gz",
        acq_time="2025-01-15T17:00:00",
        duration_sec=60.0,
    )
    result = _calc_scan_start_end_ts(r, reprostim_tz=NY, bids_tz=ZoneInfo("UTC"))
    assert result is not None
    start, end = result
    assert start == datetime(2025, 1, 15, 12, 0, 0)
    assert end == datetime(2025, 1, 15, 12, 1, 0)


def test_calc_scan_start_end_ts_none_duration_returns_none():
    r = ScanRecord(
        filename="func/test_bold.nii.gz",
        acq_time="2025-01-15T12:00:00",
        duration_sec=None,
    )
    assert _calc_scan_start_end_ts(r) is None


# ===========================================================================
# _find_bids_root
# ===========================================================================


def test_find_bids_root_dataset_description(tmp_path):
    (tmp_path / "dataset_description.json").write_text("{}")
    session_dir = tmp_path / "sub-qa" / "ses-20250814"
    session_dir.mkdir(parents=True)
    scans_file = session_dir / "sub-qa_ses-20250814_scans.tsv"
    scans_file.write_text("filename\tacq_time\n")
    assert _find_bids_root(str(scans_file)) == str(tmp_path)


def test_find_bids_root_fallback_sub_component(tmp_path):
    # No dataset_description.json — fallback uses parent of first sub- component
    session_dir = tmp_path / "sub-qa" / "ses-20250814"
    session_dir.mkdir(parents=True)
    scans_file = session_dir / "sub-qa_ses-20250814_scans.tsv"
    scans_file.write_text("filename\tacq_time\n")
    assert _find_bids_root(str(scans_file)) == str(tmp_path)


# ===========================================================================
# Integration tests (synthetic BIDS fixture)
# ===========================================================================

# Path to the static BIDS fixture committed under tests/data/bids_inject/
_BIDS_FIXTURE = Path(__file__).parent.parent / "data" / "bids_inject"
_SCANS_TSV = str(
    _BIDS_FIXTURE / "sub-qa" / "ses-20250814" / "sub-qa_ses-20250814_scans.tsv"
)

# Columns required by VaRecord / _load_tsv
_VA_HEADER = (
    "path\tpresent\tcomplete\tname\tstart_date\tstart_time\tend_date\tend_time\t"
    "video_res_detected\tvideo_fps_detected\tvideo_dur_detected\t"
    "video_res_recorded\tvideo_fps_recorded\tvideo_dur_recorded\t"
    "video_size_mb\tvideo_rate_mbpm\taudio_sr\taudio_dur\tduration\tduration_h\t"
    "no_signal_frames\tqr_records_number\tfile_log_coherent\t"
    "no_signal_updated_on\tqr_updated_on\tupdated_on"
)

# Pre-built video row strings.
# V1 covers scan 1 window [15:06:09, 15:06:29] on 2025-08-14.
_VA_V1 = (
    "video1.mkv\tTrue\tTrue\tvideo1.mkv\t2025-08-14\t15:05:00.000\t"
    "2025-08-14\t15:10:00.000\t"
    "1920x1080\t60\t300.0\t1920x1080\t60.0\tn/a\t100.0\t20.0\t"
    "48000Hz 2ch aac\tn/a\t300.0\t00:05:00.000\tn/a\tn/a\tTrue\tn/a\tn/a\t"
    "2025-08-14 15:05:00"
)
# V2 covers scan 2 window [15:13:03, 15:13:23] on 2025-08-14.
_VA_V2 = (
    "video2.mkv\tTrue\tTrue\tvideo2.mkv\t2025-08-14\t15:12:00.000\t"
    "2025-08-14\t15:17:00.000\t"
    "1920x1080\t60\t300.0\t1920x1080\t60.0\tn/a\t100.0\t20.0\t"
    "48000Hz 2ch aac\tn/a\t300.0\t00:05:00.000\tn/a\tn/a\tTrue\tn/a\tn/a\t"
    "2025-08-14 15:12:00"
)
# V3 also overlaps scan 1 window — used for the ambiguous-match test.
_VA_V3 = (
    "video3.mkv\tTrue\tTrue\tvideo3.mkv\t2025-08-14\t15:05:30.000\t"
    "2025-08-14\t15:08:00.000\t"
    "1920x1080\t60\t150.0\t1920x1080\t60.0\tn/a\t50.0\t10.0\t"
    "48000Hz 2ch aac\tn/a\t150.0\t00:02:30.000\tn/a\tn/a\tTrue\tn/a\tn/a\t"
    "2025-08-14 15:05:30"
)


def _write_videos_tsv(tmp_path: Path, *rows: str) -> str:
    """Write a videos.tsv with the given row strings and return its path."""
    content = "\n".join([_VA_HEADER] + list(rows)) + "\n"
    p = tmp_path / "videos.tsv"
    p.write_text(content)
    return str(p)


def _run(
    paths,
    videos_tsv,
    *,
    match=".*",
    dry_run=True,
    layout="nearby",
    reprostim_timezone="UTC",
    bids_timezone="UTC",
):
    """Call do_main with sensible test defaults; return (exit_code, output_lines)."""
    output = []
    ret = do_main(
        paths=paths,
        videos_tsv=videos_tsv,
        recursive=False,
        match=match,
        buffer_before="0",
        buffer_after="0",
        buffer_policy="flexible",
        time_offset=0.0,
        qr="none",
        layout=layout,
        reprostim_timezone=reprostim_timezone,
        bids_timezone=bids_timezone,
        dry_run=dry_run,
        lock=False,
        verbose=False,
        out_func=output.append,
    )
    return ret, output


def test_integration_dry_run_two_matching_videos(tmp_path):
    """Two functional scans each matched by a distinct video → 2 injected,
    1 skipped (anat)."""
    videos_tsv = _write_videos_tsv(tmp_path, _VA_V1, _VA_V2)
    ret, output = _run([_SCANS_TSV], videos_tsv)
    assert ret == 0
    summary = next(line for line in output if "injected" in line)
    assert "2 injected" in summary
    assert "1 skipped" in summary
    assert "0 errors" in summary


def test_integration_dry_run_no_matching_video(tmp_path):
    """No videos in TSV → all scans skipped, no errors."""
    videos_tsv = _write_videos_tsv(tmp_path)  # empty
    ret, output = _run([_SCANS_TSV], videos_tsv)
    assert ret == 0
    summary = next(line for line in output if "injected" in line)
    assert "0 injected" in summary
    assert "0 errors" in summary


def test_integration_dry_run_ambiguous_match(tmp_path):
    """Two videos both overlap scan 1 → ambiguous match counted as error."""
    videos_tsv = _write_videos_tsv(tmp_path, _VA_V1, _VA_V3)
    # Match only scan 1 (not the __dup-01 variant or anat)
    ret, output = _run(
        [_SCANS_TSV],
        videos_tsv,
        match=r"task-rest_acq-p2_bold\.nii\.gz$",
    )
    assert ret == 1  # non-zero because of error
    summary = next(line for line in output if "injected" in line)
    assert "0 injected" in summary
    assert "1 errors" in summary


def test_integration_dry_run_reproin_dup_suffix(tmp_path):
    """Scan with __dup-01 → output path preserves the suffix."""
    videos_tsv = _write_videos_tsv(tmp_path, _VA_V2)
    # Match only the __dup-01 scan
    ret, output = _run([_SCANS_TSV], videos_tsv, match=r"__dup-01")
    assert ret == 0
    scan_lines = [line for line in output if "[DRY-RUN] scan" in line]
    assert len(scan_lines) == 1
    output_line = next(
        line for line in output if "output" in line and "__dup-01" in line
    )
    assert "__dup-01" in output_line


def test_integration_dry_run_top_stimuli_layout(tmp_path):
    """top-stimuli layout → output path contains a stimuli/ component."""
    videos_tsv = _write_videos_tsv(tmp_path, _VA_V1)
    ret, output = _run(
        [_SCANS_TSV],
        videos_tsv,
        match=r"task-rest_acq-p2_bold\.nii\.gz$",
        layout="top-stimuli",
    )
    assert ret == 0
    output_line = next(line for line in output if "output" in line)
    assert "stimuli" in output_line


def test_integration_dry_run_match_func_only(tmp_path):
    """match=func/ → anat scan counted as skipped by filter, func scans injected."""
    videos_tsv = _write_videos_tsv(tmp_path, _VA_V1, _VA_V2)
    ret, output = _run([_SCANS_TSV], videos_tsv, match=r"^func/")
    assert ret == 0
    summary = next(line for line in output if "injected" in line)
    assert "2 injected" in summary
    assert "1 skipped" in summary  # anat filtered by --match
