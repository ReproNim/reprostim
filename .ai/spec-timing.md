# Timing Module Specification

## Overview

`src/reprostim/qr/timing.py` is a pure-library module (no CLI) that implements the ReproNim
timing-map (tmap) subsystem for multi-clock synchronisation.  It is consumed by other tools
(e.g. `qr-parse`) to convert timestamps between device clocks without those tools having to
understand the tmap file format directly.

The module provides:

- A `Clock` enum identifying the supported time sources.
- Two Pydantic models (`TPeriodData`, `TMapRecord`) that represent the structured data stored
  in `repronim_tmap.jsonl`.
- Standalone accessor functions (`get_tmap_offset`, `get_tmap_isotime`, `get_tmap_deviation`,
  `get_tmap_key`) that read fields from a `TMapRecord` in a clock-agnostic way.
- `TMapService` — the main class that loads a tmap file, computes inter-mark periods, and
  converts datetimes between clocks.
- A module-level lazy singleton (`_tmap_svc` / `get_tmap_svc()`) backed by the bundled
  `repronim_tmap.jsonl` file shipped alongside the module.

---

## Clocks

The `Clock` enum (`str, Enum`) identifies the time sources supported by the tmap system:

| Value              | Enum member         | Description                                                          |
|--------------------|---------------------|----------------------------------------------------------------------|
| `"isotime"`        | `Clock.ISOTIME`     | Reference NTP wall-clock.  The master clock; offset is always `0.0`. |
| `"birch"`          | `Clock.BIRCH`       | Birch hardware-device clock.                                         |
| `"dicoms"`         | `Clock.DICOMS`      | DICOM series acquisition clock (scanner).                            |
| `"psychopy"`       | `Clock.PSYCHOPY`    | PsychoPy stimulus-presentation software clock.                       |
| `"qrinfo"`         | `Clock.QRINFO`      | Alias for `reprostim_video`; QR code–derived timing.                 |
| `"reproevents"`    | `Clock.REPROEVENTS` | ReproEvents event-log clock.                                         |
| `"reprostim_video"`| `Clock.REPROSTIM_VIDEO` | ReproStim video-capture clock (same underlying data as `qrinfo`). |

`Clock.QRINFO` and `Clock.REPROSTIM_VIDEO` are treated identically by all accessor functions
— both map to the `reprostim_video_*` fields of `TMapRecord`.

---

## Data Models

### `TPeriodData`

Holds computed timing statistics for the interval between two consecutive tmap marks.
Produced by `TMapService.calc_periods()` and keyed by the preceding mark's `get_tmap_key`.

| Field             | Type            | Default | Description                                                                     |
|-------------------|-----------------|---------|---------------------------------------------------------------------------------|
| `key`             | `str \| None`   | `None`  | Tmap key of the *preceding* mark (back-reference into `TMapService.periods`).   |
| `duration`        | `float \| None` | `0.0`   | Period length in seconds measured on the reference (isotime) clock.             |
| `deviation`       | `float \| None` | `1.0`   | Period deviation ratio relative to the master clock (reserved; always `1.0`).   |
| `dicoms_duration` | `float \| None` | `0.0`   | Period length in seconds measured on the DICOMs clock.                          |
| `dicoms_deviation`| `float \| None` | `1.0`   | `dicoms_duration / duration` — DICOMs drift ratio for this period.              |
| `dicoms_valid`    | `bool \| None`  | `False` | `True` when no NTP correction jump was detected during this period.             |

### `TMapRecord`

One row of `repronim_tmap.jsonl`.  Each record is a synchronisation landmark anchored to
NTP time; it carries the corresponding clock readings from every device active at that moment.

**Common fields:**

| Field        | Type              | Description                                                               |
|--------------|-------------------|---------------------------------------------------------------------------|
| `isotime`    | `datetime \| None`| Reference NTP wall-clock time for this mark.                              |
| `duration`   | `float \| None`   | Duration of the mark window in seconds (isotime clock).                   |
| `session_id` | `str \| None`     | Session identifier, e.g. `ses-20240528`.                                  |
| `mark_id`    | `str \| None`     | Mark identifier within the session, e.g. `mark_000025`.                   |
| `mark_name`  | `str \| None`     | Optional human-readable label for the mark.                               |

**Per-clock fields** (pattern `<clock>_id`, `<clock>_isotime`, `<clock>_offset`,
`<clock>_duration`, `<clock>_deviation`) exist for each of: `dicoms`, `birch`, `psychopy`,
`reproevents`, and `reprostim_video`.

| Suffix        | Description                                                                                     |
|---------------|-------------------------------------------------------------------------------------------------|
| `_id`         | Dump/record identifier from that device, e.g. `dicoms-000025`.                                 |
| `_isotime`    | The device's reading expressed as an isotime-domain datetime.                                   |
| `_offset`     | Signed offset in seconds between this device's reading and `isotime` at the same mark.         |
| `_duration`   | Duration measured on the device clock for this mark window.                                     |
| `_deviation`  | Drift ratio of this device's clock relative to the master clock at this mark.                  |

Note: `qrinfo_id` is present as a standalone field but has no accompanying `qrinfo_*` time
fields — the `qrinfo` clock reuses the `reprostim_video_*` fields.

---

## Standalone Functions

### `parse_jsonl_gen(path: str) -> Generator[dict, None, None]`

Yields one `dict` per line from a JSONL file at *path*.  Uses `jsonlines.open` for
line-by-line parsing.

### `str_isotime(v: datetime) -> str | None`

Formats *v* as an ISO 8601 string `YYYY-MM-DDTHH:MM:SS.ffffff`.  Returns `None` when *v*
is falsy (e.g. `None`).

### `get_tmap_offset(clock: Clock, tmap: TMapRecord) -> float`

Returns the signed clock offset (seconds from isotime) stored in *tmap* for *clock*.
`Clock.ISOTIME` always returns `0.0`.  `Clock.QRINFO` and `Clock.REPROSTIM_VIDEO` both
return `tmap.reprostim_video_offset`.  Raises `ValueError` for an unknown clock.

### `get_tmap_isotime(clock: Clock, tmap: TMapRecord) -> datetime | None`

Returns the device-domain datetime stored in *tmap* for *clock*.  `Clock.ISOTIME` returns
`tmap.isotime`.  Raises `ValueError` for an unknown clock.

### `get_tmap_deviation(clock: Clock, tmap: TMapRecord) -> float`

Returns the drift ratio stored in *tmap* for *clock*.  `Clock.ISOTIME` always returns `1.0`.
Raises `ValueError` for an unknown clock.

### `get_tmap_key(tmap: TMapRecord) -> str`

Returns a string key of the form `"<session_id>|<mark_id>"` used to index
`TMapService.periods`.

---

## TMapService

`TMapService` loads one or more `TMapRecord` marks, computes inter-mark period statistics,
and exposes clock-conversion logic.

### `__init__(path_or_marks: str | list | None = None)`

Initialises empty `marks`, `periods`, `avg_period`, and `_force_offset` collections.
If *path_or_marks* is truthy, delegates immediately to `load`.

### `load(path_or_marks: str | list)`

Populates `marks` from either a JSONL file path or an iterable of `dict`/`TMapRecord`
objects.  After appending, sorts `marks` ascending by `isotime` and calls `calc_periods`.

### `find_tmap(clock: Clock, dt: datetime) -> TMapRecord | None`

Linear scan through sorted `marks` returning the last mark whose `<clock>_isotime ≤ dt`.
Returns `None` when `marks` is empty; returns `marks[0]` when only one mark exists.

### `convert(from_clock: Clock, to_clock: Clock, from_dt: datetime) -> datetime | None`

Converts *from_dt* from *from_clock* to *to_clock*.  Short-circuits to return *from_dt*
unchanged when the two clocks are identical or when *from_dt* is falsy.  Returns *from_dt*
unchanged (with a warning) when no tmap mark is found.

See [Algorithm: clock conversion](#algorithm-clock-conversion).

### `get_offset(clock: Clock, tmap: TMapRecord) -> float`

Returns the forced override for *clock* (if set via `force_offset`) or delegates to
`get_tmap_offset`.

### `force_offset(clock: str, offset: float | None)`

Sets a forced override offset (seconds) for *clock* (identified by its string value).
Pass `offset=None` to clear the override and revert to tmap-derived values.

> **Note:** The *clock* parameter is typed as `str` (not `Clock`), while `get_offset`
> looks up by `clock.value`.  Callers must pass the string value directly
> (e.g. `"dicoms"` not `Clock.DICOMS`).

### `adjust_offset(offset: float, clock: Clock, dt: datetime, tmap: TMapRecord) -> float`

Applies a drift correction to *offset* for the DICOMs clock only; returns *offset* unchanged
for all other clocks and when a forced override is active.

Correction formula:

```
d = (dt - tmap.isotime).total_seconds()
correction = d * period.dicoms_deviation - d
adjusted_offset = offset + correction
```

If no period is found for *tmap* (or the period is invalid), falls back to `avg_period`.

### `calc_periods()`

Populates `TMapService.periods` from consecutive mark pairs and computes `avg_period`.
See [Algorithm: period computation](#algorithm-period-computation).

### `get_period(tmap: TMapRecord) -> TPeriodData | None`

Returns the `TPeriodData` keyed by `get_tmap_key(tmap)`, or `None` if not found.

### `dump_periods()`

Logs (at `INFO`) every mark and its associated period, then the global `avg_period`.
Intended for debugging.

### `to_label() -> str`

Returns a human-readable summary:
- `"TMap is empty"` when no marks are loaded.
- `"TMap marks count N : [0]=<isotime>, [1]=<isotime>, ..."` otherwise.

---

## Module-level Singleton

```python
_tmap_svc: TMapService = None

def get_tmap_svc() -> TMapService:
    ...
```

`get_tmap_svc()` is a lazy loader that creates the singleton on first call by reading
`repronim_tmap.jsonl` from the same directory as `timing.py` (`Path(__file__).with_name(...)`).
The loaded service is cached in `_tmap_svc` for subsequent calls.

> **Known bug:** the `logger.info` line calls `get_tmap_svc().to_label()` recursively
> instead of `_tmap_svc.to_label()`.  This causes an extra (no-op) load attempt but does
> not loop because `_tmap_svc` is already set at that point.  Should be fixed to avoid
> confusion.

---

## Algorithm: Clock Conversion

`TMapService.convert(from_clock, to_clock, from_dt)` proceeds as follows:

```
1. Guard: from_clock == to_clock → return from_dt unchanged.
2. Guard: from_dt is falsy → return None.
3. tmap = find_tmap(from_clock, from_dt)
   Guard: tmap is None → warn and return from_dt unchanged.
4. from_offset = get_offset(from_clock, tmap)
   from_offset = adjust_offset(from_offset, from_clock, from_dt, tmap)
5. to_offset = get_offset(to_clock, tmap)
   to_offset = adjust_offset(to_offset, to_clock, from_dt, tmap)
6. offset = to_offset - from_offset
7. return from_dt + pandas.Timedelta(offset, unit="s")
```

The result is a `pandas.Timestamp` (a `datetime` subclass) rather than a plain `datetime`.

---

## Algorithm: Period Computation

`TMapService.calc_periods()` iterates the sorted `marks` list pairwise
(`prev_mark`, `mark`) and for each consecutive pair:

1. Computes `tp.duration = (mark.isotime - prev_mark.isotime).total_seconds()`.
2. Computes `tp.dicoms_duration = (mark.dicoms_isotime - prev_mark.dicoms_isotime).total_seconds()`.
3. Computes `tp.dicoms_deviation = dicoms_duration / duration` (when `duration != 0`).
4. Predicts the expected DICOMs offset at *mark* by extrapolating from *prev_mark*:
   ```
   expected_offset = prev_mark.dicoms_offset + duration * dicoms_deviation - dicoms_duration
   ```
5. If `|expected_offset - mark.dicoms_offset| >= 30 s`, sets `tp.dicoms_valid = False`
   (NTP clock correction detected); otherwise `True`.
6. Accumulates valid periods into a running weighted average deviation (`avg_period`):
   ```
   avg_period.dicoms_deviation += (dicoms_duration / 100) * dicoms_deviation
   ```
   After all marks: `avg_period.dicoms_deviation /= avg_period.dicoms_duration / 100`.

`avg_period` is used as a fallback in `adjust_offset` when no valid period covers the mark.

---

## File / Module Structure

| File                                         | Purpose                                         |
|----------------------------------------------|-------------------------------------------------|
| `src/reprostim/qr/timing.py`                 | Library: Clock enum, models, TMapService        |
| `src/reprostim/qr/repronim_tmap.jsonl`       | Bundled tmap data file loaded by `get_tmap_svc` |

---

## Dependencies

| Dependency   | Usage                                                         |
|--------------|---------------------------------------------------------------|
| `pydantic`   | `TPeriodData`, `TMapRecord` data models                       |
| `jsonlines`  | JSONL file parsing in `parse_jsonl_gen`                       |
| `pandas`     | `pandas.Timedelta` used in `TMapService.convert`              |

---

## Known Limitations / Open Questions

- `adjust_offset` corrects only the DICOMs clock; Birch, PsychoPy, etc. return raw offsets.
- `force_offset` accepts a plain `str` clock key while `get_offset` looks up by `clock.value`
  — the two must stay in sync manually.
- The 30-second threshold in `calc_periods` for detecting NTP jumps is hard-coded; marked as
  "tune this later" in the source.
- `get_tmap_svc()` has a recursive self-call bug in its log line (see above).
- `calc_periods` passes `valid=True` to the `TPeriodData` constructor — that field does not
  exist in the model and is silently ignored by Pydantic v2 (extra fields are ignored by
  default).  Should be removed.
- `TMapRecord` has a `qrinfo_id` field but no corresponding `qrinfo_isotime` / `qrinfo_offset`
  fields — `QRINFO` maps to `reprostim_video_*` instead.
