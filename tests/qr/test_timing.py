# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for reprostim.qr.timing."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from reprostim.qr.timing import (
    Clock,
    TMapRecord,
    TMapService,
    TPeriodData,
    get_tmap_deviation,
    get_tmap_isotime,
    get_tmap_key,
    get_tmap_offset,
    get_tmap_svc,
    parse_jsonl_gen,
    str_isotime,
)

# Absolute path to the shared tmap fixture file.
TMAP_FIXTURE = str(
    Path(__file__).parent.parent / "data" / "timing" / "repronim_tmap.jsonl"
)

# ---------------------------------------------------------------------------
# Shared in-memory mark helpers
# ---------------------------------------------------------------------------

_T0 = datetime(2024, 5, 28, 11, 0, 0)
_T1 = _T0 + timedelta(seconds=28)
_T2 = _T1 + timedelta(seconds=28)


def _make_mark(
    n: int,
    isotime: datetime,
    dicoms_offset: float = 372.0,
    session_id: str = "ses-test",
) -> dict:
    """Return a minimal but complete mark dict with controlled values."""
    dicoms_dt = isotime + timedelta(seconds=dicoms_offset)
    return {
        "isotime": isotime.isoformat(),
        "duration": 28.0,
        "session_id": session_id,
        "mark_id": f"mark-{n:06d}",
        "mark_name": f"mark_{n}",
        "dicoms_id": f"dicoms-{n:06d}",
        "dicoms_isotime": dicoms_dt.isoformat(),
        "dicoms_offset": dicoms_offset,
        "dicoms_duration": 28.0,
        "dicoms_deviation": 1.0,
        "birch_id": f"birch-{n:06d}",
        "birch_isotime": isotime.isoformat(),
        "birch_offset": 0.0,
        "birch_duration": 28.0,
        "birch_deviation": 1.0,
        "psychopy_id": f"psychopy-{n:06d}",
        "psychopy_isotime": (isotime - timedelta(seconds=0.1)).isoformat(),
        "psychopy_offset": -0.1,
        "psychopy_duration": 28.0,
        "psychopy_deviation": 1.0,
        "reproevents_id": f"reproevents-{n:06d}",
        "reproevents_isotime": (isotime - timedelta(seconds=0.05)).isoformat(),
        "reproevents_offset": -0.05,
        "reproevents_duration": 28.0,
        "reproevents_deviation": 1.0,
        "qrinfo_id": f"qrinfo-{n:06d}",
        "reprostim_video_isotime": (isotime + timedelta(seconds=0.2)).isoformat(),
        "reprostim_video_offset": 0.2,
        "reprostim_video_duration": 28.0,
        "reprostim_video_deviation": 1.0,
    }


# Two-mark and three-mark datasets (same dicoms_offset → deviation=1.0)
_MARKS_2 = [_make_mark(1, _T0), _make_mark(2, _T1)]
_MARKS_3 = [_make_mark(1, _T0), _make_mark(2, _T1), _make_mark(3, _T2)]

# Two marks where mark2 has a slight dicoms drift (offset differs by 0.028 s)
_MARKS_DRIFT = [
    _make_mark(1, _T0, dicoms_offset=372.0),
    _make_mark(2, _T1, dicoms_offset=372.028),
]

# Two marks simulating an NTP clock correction (offset jumps by ~400 s)
_MARKS_JUMP = [
    _make_mark(10, _T0, dicoms_offset=370.0),
    _make_mark(11, _T1, dicoms_offset=-27.0),
]


# ===========================================================================
# Clock
# ===========================================================================


def test_clock_all_members_accessible_by_value():
    """All seven Clock members are reachable via their string value."""
    expected = {
        "isotime": Clock.ISOTIME,
        "birch": Clock.BIRCH,
        "dicoms": Clock.DICOMS,
        "psychopy": Clock.PSYCHOPY,
        "qrinfo": Clock.QRINFO,
        "reproevents": Clock.REPROEVENTS,
        "reprostim_video": Clock.REPROSTIM_VIDEO,
    }
    for value, member in expected.items():
        assert Clock(value) is member


def test_clock_is_str_enum():
    """Clock members behave as strings."""
    assert Clock.ISOTIME == "isotime"
    assert Clock.DICOMS == "dicoms"


# ===========================================================================
# str_isotime
# ===========================================================================


def test_str_isotime_known_datetime():
    """Known datetime is formatted as expected ISO 8601 string."""
    dt = datetime(2024, 5, 28, 11, 9, 0, 647672)
    assert str_isotime(dt) == "2024-05-28T11:09:00.647672"


def test_str_isotime_none_returns_none():
    """None input returns None."""
    assert str_isotime(None) is None


def test_str_isotime_falsy_zero_returns_none():
    """Falsy non-None value returns None."""
    assert str_isotime(0) is None


# ===========================================================================
# parse_jsonl_gen
# ===========================================================================


def test_parse_jsonl_gen_yields_dicts():
    """parse_jsonl_gen yields dict objects from the fixture file."""
    records = list(parse_jsonl_gen(TMAP_FIXTURE))
    assert len(records) > 0
    assert all(isinstance(r, dict) for r in records)


def test_parse_jsonl_gen_fixture_record_count():
    """Fixture file contains the expected number of records."""
    records = list(parse_jsonl_gen(TMAP_FIXTURE))
    assert len(records) == 13


def test_parse_jsonl_gen_records_have_isotime():
    """Every record in the fixture has an 'isotime' key."""
    for rec in parse_jsonl_gen(TMAP_FIXTURE):
        assert "isotime" in rec


# ===========================================================================
# get_tmap_key
# ===========================================================================


def test_get_tmap_key_composite_format():
    """get_tmap_key returns 'session_id|mark_id'."""
    rec = TMapRecord(session_id="ses-20240528", mark_id="mark-000022")
    assert get_tmap_key(rec) == "ses-20240528|mark-000022"


def test_get_tmap_key_with_none_fields():
    """get_tmap_key works when fields are None."""
    rec = TMapRecord()
    assert get_tmap_key(rec) == "None|None"


# ===========================================================================
# get_tmap_offset
# ===========================================================================


def test_get_tmap_offset_isotime_returns_zero():
    """Clock.ISOTIME offset is always 0.0."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_offset(Clock.ISOTIME, rec) == pytest.approx(0.0)


def test_get_tmap_offset_birch():
    """Clock.BIRCH returns birch_offset."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_offset(Clock.BIRCH, rec) == pytest.approx(rec.birch_offset)


def test_get_tmap_offset_dicoms():
    """Clock.DICOMS returns dicoms_offset."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_offset(Clock.DICOMS, rec) == pytest.approx(rec.dicoms_offset)


def test_get_tmap_offset_psychopy():
    """Clock.PSYCHOPY returns psychopy_offset."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_offset(Clock.PSYCHOPY, rec) == pytest.approx(rec.psychopy_offset)


def test_get_tmap_offset_reproevents():
    """Clock.REPROEVENTS returns reproevents_offset."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_offset(Clock.REPROEVENTS, rec) == pytest.approx(
        rec.reproevents_offset
    )


def test_get_tmap_offset_qrinfo():
    """Clock.QRINFO returns reprostim_video_offset."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_offset(Clock.QRINFO, rec) == pytest.approx(
        rec.reprostim_video_offset
    )


def test_get_tmap_offset_reprostim_video():
    """Clock.REPROSTIM_VIDEO returns reprostim_video_offset."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_offset(Clock.REPROSTIM_VIDEO, rec) == pytest.approx(
        rec.reprostim_video_offset
    )


def test_get_tmap_offset_qrinfo_equals_reprostim_video():
    """Clock.QRINFO and Clock.REPROSTIM_VIDEO return the same value."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_offset(Clock.QRINFO, rec) == get_tmap_offset(
        Clock.REPROSTIM_VIDEO, rec
    )


def test_get_tmap_offset_unknown_raises():
    """An unknown clock string raises ValueError."""
    rec = TMapRecord(**_make_mark(1, _T0))
    with pytest.raises(ValueError):
        get_tmap_offset("unknown_clock", rec)


# ===========================================================================
# get_tmap_isotime
# ===========================================================================


def test_get_tmap_isotime_isotime():
    """Clock.ISOTIME returns tmap.isotime."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_isotime(Clock.ISOTIME, rec) == rec.isotime


def test_get_tmap_isotime_birch():
    """Clock.BIRCH returns birch_isotime."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_isotime(Clock.BIRCH, rec) == rec.birch_isotime


def test_get_tmap_isotime_dicoms():
    """Clock.DICOMS returns dicoms_isotime."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_isotime(Clock.DICOMS, rec) == rec.dicoms_isotime


def test_get_tmap_isotime_psychopy():
    """Clock.PSYCHOPY returns psychopy_isotime."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_isotime(Clock.PSYCHOPY, rec) == rec.psychopy_isotime


def test_get_tmap_isotime_reproevents():
    """Clock.REPROEVENTS returns reproevents_isotime."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_isotime(Clock.REPROEVENTS, rec) == rec.reproevents_isotime


def test_get_tmap_isotime_qrinfo():
    """Clock.QRINFO returns reprostim_video_isotime."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_isotime(Clock.QRINFO, rec) == rec.reprostim_video_isotime


def test_get_tmap_isotime_reprostim_video():
    """Clock.REPROSTIM_VIDEO returns reprostim_video_isotime."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_isotime(Clock.REPROSTIM_VIDEO, rec) == rec.reprostim_video_isotime


def test_get_tmap_isotime_unknown_raises():
    """An unknown clock string raises ValueError."""
    rec = TMapRecord(**_make_mark(1, _T0))
    with pytest.raises(ValueError):
        get_tmap_isotime("unknown_clock", rec)


# ===========================================================================
# get_tmap_deviation
# ===========================================================================


def test_get_tmap_deviation_isotime_returns_one():
    """Clock.ISOTIME deviation is always 1.0."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_deviation(Clock.ISOTIME, rec) == pytest.approx(1.0)


def test_get_tmap_deviation_birch():
    """Clock.BIRCH returns birch_deviation."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_deviation(Clock.BIRCH, rec) == pytest.approx(rec.birch_deviation)


def test_get_tmap_deviation_dicoms():
    """Clock.DICOMS returns dicoms_deviation."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_deviation(Clock.DICOMS, rec) == pytest.approx(rec.dicoms_deviation)


def test_get_tmap_deviation_psychopy():
    """Clock.PSYCHOPY returns psychopy_deviation."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_deviation(Clock.PSYCHOPY, rec) == pytest.approx(
        rec.psychopy_deviation
    )


def test_get_tmap_deviation_reproevents():
    """Clock.REPROEVENTS returns reproevents_deviation."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_deviation(Clock.REPROEVENTS, rec) == pytest.approx(
        rec.reproevents_deviation
    )


def test_get_tmap_deviation_qrinfo():
    """Clock.QRINFO returns reprostim_video_deviation."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_deviation(Clock.QRINFO, rec) == pytest.approx(
        rec.reprostim_video_deviation
    )


def test_get_tmap_deviation_reprostim_video():
    """Clock.REPROSTIM_VIDEO returns reprostim_video_deviation."""
    rec = TMapRecord(**_make_mark(1, _T0))
    assert get_tmap_deviation(Clock.REPROSTIM_VIDEO, rec) == pytest.approx(
        rec.reprostim_video_deviation
    )


def test_get_tmap_deviation_unknown_raises():
    """An unknown clock string raises ValueError."""
    rec = TMapRecord(**_make_mark(1, _T0))
    with pytest.raises(ValueError):
        get_tmap_deviation("unknown_clock", rec)


# ===========================================================================
# TPeriodData
# ===========================================================================


def test_tperiod_data_defaults():
    """TPeriodData fields default to expected values."""
    tp = TPeriodData()
    assert tp.key is None
    assert tp.duration == pytest.approx(0.0)
    assert tp.deviation == pytest.approx(1.0)
    assert tp.dicoms_duration == pytest.approx(0.0)
    assert tp.dicoms_deviation == pytest.approx(1.0)
    assert tp.dicoms_valid is False


def test_tperiod_data_explicit_values():
    """TPeriodData stores explicit values correctly."""
    tp = TPeriodData(key="ses-x|mark-001", duration=28.0, dicoms_valid=True)
    assert tp.key == "ses-x|mark-001"
    assert tp.duration == pytest.approx(28.0)
    assert tp.dicoms_valid is True


# ===========================================================================
# TMapService.__init__
# ===========================================================================


def test_tmap_service_init_empty():
    """Empty TMapService starts with no marks, no periods, default avg_period."""
    svc = TMapService()
    assert svc.marks == []
    assert svc.periods == {}
    assert isinstance(svc.avg_period, TPeriodData)


def test_tmap_service_init_with_list():
    """TMapService(list) loads marks immediately."""
    svc = TMapService(_MARKS_2)
    assert len(svc.marks) == 2


def test_tmap_service_init_with_path():
    """TMapService(path) loads marks from a JSONL file."""
    svc = TMapService(TMAP_FIXTURE)
    assert len(svc.marks) == 13


# ===========================================================================
# TMapService.load
# ===========================================================================


def test_load_from_list_sorts_by_isotime():
    """Marks loaded from a list are sorted ascending by isotime."""
    # Provide out-of-order marks (T1 before T0)
    svc = TMapService([_make_mark(2, _T1), _make_mark(1, _T0)])
    assert svc.marks[0].isotime < svc.marks[1].isotime


def test_load_from_file_produces_correct_count():
    """Marks loaded from fixture file match the expected record count."""
    svc = TMapService()
    svc.load(TMAP_FIXTURE)
    assert len(svc.marks) == 13


def test_load_appends_on_successive_calls():
    """Calling load twice appends marks and re-sorts."""
    svc = TMapService(_MARKS_2)
    svc.load([_make_mark(3, _T2)])
    assert len(svc.marks) == 3


# ===========================================================================
# TMapService.find_tmap
# ===========================================================================


def test_find_tmap_empty_returns_none():
    """find_tmap returns None when no marks are loaded."""
    svc = TMapService()
    assert svc.find_tmap(Clock.ISOTIME, _T0) is None


def test_find_tmap_single_mark_always_returned():
    """find_tmap returns the only mark regardless of dt."""
    svc = TMapService([_make_mark(1, _T0)])
    assert svc.find_tmap(Clock.ISOTIME, _T0 - timedelta(hours=1)) is svc.marks[0]
    assert svc.find_tmap(Clock.ISOTIME, _T0 + timedelta(hours=1)) is svc.marks[0]


def test_find_tmap_dt_before_first_mark():
    """dt earlier than all marks returns the first mark."""
    svc = TMapService(_MARKS_3)
    result = svc.find_tmap(Clock.ISOTIME, _T0 - timedelta(seconds=1))
    assert result is svc.marks[0]


def test_find_tmap_dt_between_marks():
    """dt between mark1 and mark2 returns mark1."""
    svc = TMapService(_MARKS_3)
    dt_between = _T0 + timedelta(seconds=14)
    result = svc.find_tmap(Clock.ISOTIME, dt_between)
    assert result.mark_id == "mark-000001"


def test_find_tmap_dt_after_all_marks():
    """dt after all marks returns the last mark."""
    svc = TMapService(_MARKS_3)
    result = svc.find_tmap(Clock.ISOTIME, _T2 + timedelta(hours=1))
    assert result is svc.marks[-1]


def test_find_tmap_uses_clock_isotime_field():
    """find_tmap searches by the correct clock-specific isotime field."""
    svc = TMapService(_MARKS_2)
    # BIRCH isotimes equal isotime; REPROSTIM_VIDEO isotimes are 0.2 s later
    dt = _T0 + timedelta(seconds=0.1)  # after birch[0] but before video[0]
    birch_result = svc.find_tmap(Clock.BIRCH, dt)
    video_result = svc.find_tmap(Clock.REPROSTIM_VIDEO, dt)
    # birch[0].isotime = T0 ≤ T0+0.1 → last_mark = marks[0]
    assert birch_result is svc.marks[0]
    # video[0].isotime = T0+0.2 > T0+0.1 → breaks immediately, last_mark = marks[0]
    assert video_result is svc.marks[0]


# ===========================================================================
# TMapService.calc_periods
# ===========================================================================


def test_calc_periods_two_marks_valid():
    """Two marks with consistent offsets produce a valid period with deviation 1.0."""
    svc = TMapService(_MARKS_2)
    key = get_tmap_key(svc.marks[0])
    assert key in svc.periods
    tp = svc.periods[key]
    assert tp.dicoms_valid is True
    assert tp.dicoms_deviation == pytest.approx(1.0)
    assert tp.duration == pytest.approx(28.0)


def test_calc_periods_drift_deviation():
    """Two marks with a 0.028 s DICOMS offset drift produce dicoms_deviation ≈ 1.001."""
    svc = TMapService(_MARKS_DRIFT)
    key = get_tmap_key(svc.marks[0])
    tp = svc.periods[key]
    assert tp.dicoms_valid is True
    assert tp.dicoms_deviation == pytest.approx(1.001, rel=1e-3)


def test_calc_periods_large_offset_jump_invalid():
    """A >30 s DICOMS offset jump between marks flags the period as invalid."""
    svc = TMapService(_MARKS_JUMP)
    key = get_tmap_key(svc.marks[0])
    tp = svc.periods[key]
    assert tp.dicoms_valid is False


def test_calc_periods_single_mark_no_periods():
    """A single mark produces no periods."""
    svc = TMapService([_make_mark(1, _T0)])
    assert svc.periods == {}


def test_calc_periods_zero_duration_skips_deviation():
    """Two marks with identical isotime produce a period with default
    dicoms_deviation."""
    svc = TMapService([_make_mark(1, _T0), _make_mark(2, _T0)])
    key = get_tmap_key(svc.marks[0])
    tp = svc.periods[key]
    # duration = 0 → the dicoms_deviation assignment is skipped; default stays 1.0
    assert tp.duration == pytest.approx(0.0)
    assert tp.dicoms_deviation == pytest.approx(1.0)


def test_calc_periods_avg_period_populated():
    """avg_period is non-default after loading valid marks."""
    svc = TMapService(_MARKS_2)
    assert svc.avg_period.duration == pytest.approx(28.0, abs=0.1)


# ===========================================================================
# TMapService.get_period
# ===========================================================================


def test_get_period_found():
    """get_period returns TPeriodData for a mark that has an associated period."""
    svc = TMapService(_MARKS_2)
    tp = svc.get_period(svc.marks[0])
    assert tp is not None
    assert isinstance(tp, TPeriodData)


def test_get_period_not_found_for_last_mark():
    """get_period returns None for the last mark (no following period)."""
    svc = TMapService(_MARKS_2)
    assert svc.get_period(svc.marks[-1]) is None


def test_get_period_not_found_unknown_key():
    """get_period returns None for a record whose key is not in periods."""
    svc = TMapService(_MARKS_2)
    orphan = TMapRecord(session_id="ses-unknown", mark_id="mark-999")
    assert svc.get_period(orphan) is None


# ===========================================================================
# TMapService.force_offset / get_offset
# ===========================================================================


def test_force_offset_clear_nonexistent_is_noop():
    """Clearing a forced offset that was never set is a silent no-op."""
    svc = TMapService(_MARKS_2)
    svc.force_offset("dicoms", None)  # nothing to clear — must not raise
    assert svc._force_offset == {}


def test_force_offset_set_overrides_tmap_value():
    """force_offset causes get_offset to return the forced value."""
    svc = TMapService(_MARKS_2)
    mark = svc.marks[0]
    svc.force_offset("dicoms", 999.0)
    assert svc.get_offset(Clock.DICOMS, mark) == pytest.approx(999.0)


def test_force_offset_clear_restores_tmap_value():
    """Clearing a forced offset (passing None) restores the tmap-derived value."""
    svc = TMapService(_MARKS_2)
    mark = svc.marks[0]
    svc.force_offset("dicoms", 999.0)
    svc.force_offset("dicoms", None)
    assert svc.get_offset(Clock.DICOMS, mark) == pytest.approx(372.0)


def test_get_offset_no_force_returns_tmap_field():
    """Without a forced override get_offset delegates to get_tmap_offset."""
    svc = TMapService(_MARKS_2)
    mark = svc.marks[0]
    assert svc.get_offset(Clock.DICOMS, mark) == pytest.approx(mark.dicoms_offset)
    assert svc.get_offset(Clock.ISOTIME, mark) == pytest.approx(0.0)


# ===========================================================================
# TMapService.adjust_offset
# ===========================================================================


def test_adjust_offset_non_dicoms_clock_unchanged():
    """adjust_offset returns the offset unchanged for non-DICOMS clocks."""
    svc = TMapService(_MARKS_2)
    mark = svc.marks[0]
    assert svc.adjust_offset(5.0, Clock.BIRCH, _T0, mark) == pytest.approx(5.0)
    assert svc.adjust_offset(5.0, Clock.ISOTIME, _T0, mark) == pytest.approx(5.0)
    assert svc.adjust_offset(5.0, Clock.PSYCHOPY, _T0, mark) == pytest.approx(5.0)


def test_adjust_offset_dicoms_with_forced_offset_unchanged():
    """adjust_offset returns the offset unchanged when a forced
    DICOMS override is set."""
    svc = TMapService(_MARKS_2)
    svc.force_offset("dicoms", 500.0)
    mark = svc.marks[0]
    assert svc.adjust_offset(
        372.0, Clock.DICOMS, _T0 + timedelta(seconds=10), mark
    ) == pytest.approx(372.0)


def test_adjust_offset_dicoms_zero_elapsed_no_correction():
    """adjust_offset applies zero correction when dt equals tmap.isotime (d=0)."""
    svc = TMapService(_MARKS_2)
    mark = svc.marks[0]
    # dt == mark.isotime → d = 0 → correction = 0
    result = svc.adjust_offset(372.0, Clock.DICOMS, _T0, mark)
    assert result == pytest.approx(372.0)


def test_adjust_offset_dicoms_uses_period_deviation():
    """adjust_offset applies drift correction using the period's dicoms_deviation."""
    svc = TMapService(_MARKS_DRIFT)
    mark = svc.marks[0]
    tp = svc.get_period(mark)
    assert tp is not None and tp.dicoms_valid

    d = 10.0
    dt = _T0 + timedelta(seconds=d)
    expected_correction = d * tp.dicoms_deviation - d
    result = svc.adjust_offset(372.0, Clock.DICOMS, dt, mark)
    assert result == pytest.approx(372.0 + expected_correction, rel=1e-6)


def test_adjust_offset_dicoms_no_period_falls_back_to_avg():
    """adjust_offset uses avg_period when the mark has no associated period."""
    svc = TMapService(_MARKS_2)
    last_mark = svc.marks[-1]  # last mark has no period
    assert svc.get_period(last_mark) is None
    # With avg_period.dicoms_deviation the correction is non-zero for d > 0
    d = 5.0
    dt = last_mark.isotime + timedelta(seconds=d)
    result = svc.adjust_offset(372.0, Clock.DICOMS, dt, last_mark)
    correction = d * svc.avg_period.dicoms_deviation - d
    assert result == pytest.approx(372.0 + correction, rel=1e-6)


def test_adjust_offset_dicoms_invalid_period_falls_back_to_avg():
    """adjust_offset falls back to avg_period when the period is flagged invalid."""
    svc = TMapService(_MARKS_JUMP)
    mark = svc.marks[0]
    tp = svc.get_period(mark)
    assert tp is not None and tp.dicoms_valid is False

    d = 5.0
    dt = mark.isotime + timedelta(seconds=d)
    result = svc.adjust_offset(370.0, Clock.DICOMS, dt, mark)
    correction = d * svc.avg_period.dicoms_deviation - d
    assert result == pytest.approx(370.0 + correction, rel=1e-6)


# ===========================================================================
# TMapService.convert
# ===========================================================================


def test_convert_same_clock_returns_dt_unchanged():
    """convert returns from_dt unchanged when both clocks are identical."""
    svc = TMapService(_MARKS_2)
    result = svc.convert(Clock.ISOTIME, Clock.ISOTIME, _T0)
    assert result == _T0


def test_convert_falsy_dt_returns_none():
    """convert returns None when from_dt is falsy."""
    svc = TMapService(_MARKS_2)
    assert svc.convert(Clock.ISOTIME, Clock.DICOMS, None) is None


def test_convert_no_marks_returns_dt_unchanged():
    """convert returns from_dt unchanged (with warning) when marks list is empty."""
    svc = TMapService()
    result = svc.convert(Clock.ISOTIME, Clock.DICOMS, _T0)
    assert result == _T0


def test_convert_isotime_to_dicoms():
    """convert(ISOTIME→DICOMS) shifts dt by the dicoms_offset of the anchor mark."""
    svc = TMapService(_MARKS_2)
    # dt == mark1.isotime → d = 0 → no drift correction → pure offset shift
    result = svc.convert(Clock.ISOTIME, Clock.DICOMS, _T0)
    expected = _T0 + timedelta(seconds=372.0)
    assert abs((result - expected).total_seconds()) < 1e-6


def test_convert_dicoms_to_isotime():
    """convert(DICOMS→ISOTIME) shifts dt back by the dicoms_offset of the anchor mark."""
    svc = TMapService(_MARKS_2)
    dicoms_dt = _T0 + timedelta(seconds=372.0)
    result = svc.convert(Clock.DICOMS, Clock.ISOTIME, dicoms_dt)
    # d = (dicoms_dt - mark1.isotime).total_seconds() = 372.0
    # correction = 372.0 * 1.0 - 372.0 = 0  (deviation = 1.0)
    # offset = 0.0 - 372.0 = -372.0
    expected = dicoms_dt + timedelta(seconds=-372.0)
    assert abs((result - expected).total_seconds()) < 1e-6


def test_convert_with_forced_offset():
    """convert respects a forced offset override."""
    svc = TMapService(_MARKS_2)
    svc.force_offset("dicoms", 100.0)
    result = svc.convert(Clock.ISOTIME, Clock.DICOMS, _T0)
    expected = _T0 + timedelta(seconds=100.0)
    assert abs((result - expected).total_seconds()) < 1e-6


def test_convert_birch_to_isotime_zero_offset():
    """Birch and ISOTIME share the same clock in the test marks;
    result equals from_dt."""
    svc = TMapService(_MARKS_2)
    result = svc.convert(Clock.BIRCH, Clock.ISOTIME, _T0)
    expected = _T0 + timedelta(seconds=0.0 - 0.0)  # birch_offset - isotime_offset
    assert abs((result - expected).total_seconds()) < 1e-6


# ===========================================================================
# TMapService.dump_periods
# ===========================================================================


def test_dump_periods_no_exception():
    """dump_periods runs without raising regardless of mark count."""
    TMapService().dump_periods()
    TMapService(_MARKS_2).dump_periods()


# ===========================================================================
# TMapService.to_label
# ===========================================================================


def test_to_label_empty():
    """to_label returns 'TMap is empty' when no marks are loaded."""
    assert TMapService().to_label() == "TMap is empty"


def test_to_label_one_mark_contains_isotime():
    """to_label includes the mark's isotime for a single-mark service."""
    svc = TMapService([_make_mark(1, _T0)])
    label = svc.to_label()
    assert "TMap marks count 1" in label
    assert str_isotime(_T0) in label


def test_to_label_multiple_marks():
    """to_label reports the correct count and lists all mark isotimes."""
    svc = TMapService(_MARKS_3)
    label = svc.to_label()
    assert "TMap marks count 3" in label
    for m in svc.marks:
        assert str_isotime(m.isotime) in label


# ===========================================================================
# get_tmap_svc
# ===========================================================================


def test_get_tmap_svc_returns_tmap_service(monkeypatch):
    """get_tmap_svc loads marks from the fixture file and returns a TMapService."""
    import reprostim.qr.timing as timing_mod

    monkeypatch.setattr(timing_mod, "_tmap_svc", None)
    monkeypatch.setattr(timing_mod, "TMAP_FILENAME", TMAP_FIXTURE)

    svc = get_tmap_svc()
    assert isinstance(svc, TMapService)
    assert len(svc.marks) == 13


def test_get_tmap_svc_singleton(monkeypatch):
    """get_tmap_svc returns the same instance on every call."""
    import reprostim.qr.timing as timing_mod

    monkeypatch.setattr(timing_mod, "_tmap_svc", None)
    monkeypatch.setattr(timing_mod, "TMAP_FILENAME", TMAP_FIXTURE)

    svc1 = get_tmap_svc()
    svc2 = get_tmap_svc()
    assert svc1 is svc2


def test_get_tmap_svc_loads_from_cwd_when_filename_only(monkeypatch, tmp_path):
    """get_tmap_svc picks up a plain filename from the current working directory."""
    import shutil

    import reprostim.qr.timing as timing_mod

    # Place a copy of the fixture in a temp directory and make it the CWD.
    dest = tmp_path / "repronim_tmap.jsonl"
    shutil.copy(TMAP_FIXTURE, dest)

    monkeypatch.setattr(timing_mod, "_tmap_svc", None)
    monkeypatch.setattr(timing_mod, "TMAP_FILENAME", "repronim_tmap.jsonl")
    monkeypatch.chdir(tmp_path)

    svc = get_tmap_svc()
    assert isinstance(svc, TMapService)
    assert len(svc.marks) == 13


def test_get_tmap_svc_cached_instance_not_reloaded(monkeypatch):
    """get_tmap_svc skips loading when a cached instance is already set."""
    import reprostim.qr.timing as timing_mod

    sentinel = TMapService(_MARKS_2)
    monkeypatch.setattr(timing_mod, "_tmap_svc", sentinel)

    result = get_tmap_svc()
    assert result is sentinel
