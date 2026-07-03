# `timing` Task List

Tracks implementation and documentation progress against [spec-timing.md](spec-timing.md).

---

## Data Models

- [x] `Clock` enum — 7 values (`isotime`, `birch`, `dicoms`, `psychopy`, `qrinfo`, `reproevents`, `reprostim_video`)
- [x] `TPeriodData` pydantic model — 6 fields (`key`, `duration`, `deviation`, `dicoms_duration`, `dicoms_deviation`, `dicoms_valid`)
- [x] `TMapRecord` pydantic model — common fields + per-clock `_id`, `_isotime`, `_offset`, `_duration`, `_deviation` fields for all 5 device clocks

---

## Standalone Functions

- [x] `parse_jsonl_gen(path)` — JSONL file → generator of dicts via `jsonlines`
- [x] `str_isotime(v)` — datetime → `YYYY-MM-DDTHH:MM:SS.ffffff` string; returns `None` for falsy input
- [x] `get_tmap_offset(clock, tmap)` — returns offset field for given clock; `ISOTIME` → `0.0`; raises `ValueError` for unknown clock
- [x] `get_tmap_isotime(clock, tmap)` — returns isotime field for given clock; raises `ValueError` for unknown clock
- [x] `get_tmap_deviation(clock, tmap)` — returns deviation field for given clock; `ISOTIME` → `1.0`; raises `ValueError` for unknown clock
- [x] `get_tmap_key(tmap)` — returns `"<session_id>|<mark_id>"` composite key

---

## TMapService

- [x] `__init__(path_or_marks)` — initialises `marks`, `periods`, `avg_period`, `_force_offset`; calls `load` when arg is truthy
- [x] `load(path_or_marks)` — reads JSONL file or list of dicts; appends `TMapRecord` objects; sorts by `isotime`; calls `calc_periods`
- [x] `find_tmap(clock, dt)` — linear scan returning last mark whose `<clock>_isotime ≤ dt`; handles 0- and 1-mark edge cases
- [x] `convert(from_clock, to_clock, from_dt)` — full clock conversion via tmap marks with `adjust_offset` correction
- [x] `get_offset(clock, tmap)` — returns forced override (if set) or delegates to `get_tmap_offset`
- [x] `force_offset(clock, offset)` — set / clear a forced override for a clock (stored by `clock.value` string)
- [x] `adjust_offset(offset, clock, dt, tmap)` — DICOMs-only drift correction using period deviation; returns offset unchanged for all other clocks
- [x] `calc_periods()` — pairwise inter-mark period computation; `dicoms_deviation`, `dicoms_valid` flag, weighted `avg_period`
- [x] `get_period(tmap)` — looks up `TPeriodData` by `get_tmap_key(tmap)`; returns `None` when absent
- [x] `dump_periods()` — logs all marks, their periods, and `avg_period` at `INFO` level (debug helper)
- [x] `to_label()` — human-readable summary of mark count and isotimes; `"TMap is empty"` when no marks

---

## Module-level Singleton

- [x] `_tmap_svc` — module-level variable initialised to `None`
- [x] `TMAP_FILENAME` — module-level constant `"repronim_tmap.jsonl"` (file name of the bundled tmap)
- [x] `get_tmap_svc()` — lazy loader; reads bundled `TMAP_FILENAME` on first call; caches in `_tmap_svc`

---

## Documentation

- [x] Module docstring
- [x] `Clock` class docstring
- [x] `TPeriodData` class docstring
- [x] `TMapRecord` class docstring
- [x] `TMapService` class docstring
- [x] Docstrings for all standalone functions (`parse_jsonl_gen`, `str_isotime`, `get_tmap_offset`, `get_tmap_isotime`, `get_tmap_deviation`, `get_tmap_key`)
- [x] Docstrings for all `TMapService` methods
- [x] `get_tmap_svc` function docstring

---

## Bug Fixes

- [x] `calc_periods`: removed `valid=True` kwarg from `TPeriodData()` — field does not exist in the model
- [x] `get_tmap_svc()`: replaced recursive `get_tmap_svc().to_label()` log call with `_tmap_svc.to_label()`
- [ ] `force_offset` / `get_offset` API mismatch: `force_offset` takes `clock: str` but `get_offset` looks up by `clock.value` — document or unify

---

## Tests

Test file location: `tests/qr/test_timing.py` (to be created).

- [ ] `Clock` enum — all 7 members accessible by value
- [ ] `str_isotime` — known `datetime` → expected ISO string
- [ ] `str_isotime` — falsy input (`None`) → `None`
- [ ] `get_tmap_key` — returns `"session_id|mark_id"` for a known record
- [ ] `get_tmap_offset` — each `Clock` value returns the correct `TMapRecord` field
- [ ] `get_tmap_offset` — `Clock.QRINFO` and `Clock.REPROSTIM_VIDEO` return the same value
- [ ] `get_tmap_isotime` — each `Clock` value returns the correct `TMapRecord` field
- [ ] `get_tmap_deviation` — `Clock.ISOTIME` → `1.0`; other clocks return model field
- [ ] `TMapService.__init__` — empty init: `marks == []`, `periods == {}`, no error
- [ ] `TMapService.load` from list of dicts — marks sorted ascending by `isotime`
- [ ] `TMapService.find_tmap` — correct mark returned for a datetime between two marks
- [ ] `TMapService.find_tmap` — datetime before first mark returns first mark
- [ ] `TMapService.find_tmap` — empty service returns `None`
- [ ] `TMapService.convert` — same-clock: returns `from_dt` unchanged
- [ ] `TMapService.convert` — falsy `from_dt`: returns `None`
- [ ] `TMapService.convert` — known two-mark dataset with known DICOMs offset → correct shifted result
- [ ] `TMapService.force_offset` — set: `get_offset` returns override value
- [ ] `TMapService.force_offset` — clear (`None`): `get_offset` returns tmap field value
- [ ] `TMapService.calc_periods` — two-mark case: `dicoms_deviation` and `dicoms_valid` computed correctly
- [ ] `TMapService.to_label` — empty service → `"TMap is empty"`
- [ ] `TMapService.to_label` — one mark → string contains isotime

---

## Open Questions / Future Work

- [ ] Extend `adjust_offset` to support clocks beyond DICOMs
- [ ] Unify `force_offset` / `get_offset` API to use `Clock` enum consistently
- [ ] Make the NTP-jump threshold (30 s) in `calc_periods` configurable
- [ ] Consider replacing `pandas.Timedelta` in `convert` with `datetime.timedelta` to remove the `pandas` dependency from this module
- [ ] Expose `TMapService` via CLI for debugging (e.g. `reprostim tmap-info`)
- [ ] Add path override for `get_tmap_svc()` (environment variable or config) instead of hard-coded file path
