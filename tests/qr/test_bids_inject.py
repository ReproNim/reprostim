# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for the Datetime / Timezone public API in reprostim.qr.bids_inject."""

import re
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytest

from reprostim.qr.bids_inject import (
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
