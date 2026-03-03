# `bids-inject` Task List

Tracks implementation progress against [spec-bids-inject.md](spec-bids-inject.md).

---

## CLI Options

- [x] `PATHS` argument — one or more `_scans.tsv` files or directories
- [x] `-f / --videos` — path to `videos.tsv`
- [x] `-r / --recursive` — recurse into subdirectories
- [x] `-b / --buffer-before` — extra video before scan onset
- [x] `-a / --buffer-after` — extra video after scan end
- [x] `-p / --buffer-policy [strict|flexible]`
- [x] `-t / --time-offset` — clock offset in seconds
- [ ] `-q / --qr [none|auto|embed-existing|parse]` — option defined; logic not yet implemented
- [x] `-l / --layout [nearby|top-stimuli]`
- [x] `-z / --reprostim-timezone` — timezone for `videos.tsv` timestamps
- [x] `-Z / --bids-timezone` — timezone for BIDS `acq_time` values
- [x] `-m / --match REGEX` — filter scan records by filename
- [x] `-d / --dry-run`
- [x] `-k / --lock [yes|no]` — dirty-read mode for `videos.tsv`
- [x] `-v / --verbose`

---

## Core Logic

### Path / file handling
- [x] Process a single `_scans.tsv` file directly
- [x] Scan a directory for `*_scans.tsv` files (non-recursive)
- [x] Recursive directory traversal (`--recursive`)
- [x] Mixed list of files and directories in a single invocation

### videos.tsv integration
- [x] Load `videos.tsv` and resolve video paths relative to its location
- [x] Match video records by time range (`find_video_audit_by_timerange`)
- [x] Skip records where `present = False`
- [x] Warn on records where `complete = False`
- [x] Lock / dirty-read mode (`--lock no` bypasses `FileLock`)

### _scans.tsv integration
- [x] Parse `_scans.tsv` (`filename` + `acq_time` columns)
- [x] Apply `--match` regex to filter scan records
- [ ] Filter: skip non-functional scans (those not starting with `func/`)
- [ ] Filter: skip single-volume acquisitions (4th NIfTI dimension < 2)

### Scan duration computation
- [x] Priority 1: `FrameAcquisitionDuration` (ms → seconds)
- [x] Priority 2: `AcquisitionTime` array — `(t_last − t_first) + TR`
- [x] Priority 3: `RepetitionTime × NumberOfVolumes`
- [x] Warn and skip when duration cannot be determined
- [ ] `--duration` manual override option (future)

### Timezone handling
- [x] `dt_resolve_tz` — string → `tzinfo` (with `lru_cache`)
- [x] `dt_parse_bids` — ISO 8601 string → naive `datetime`
- [x] `dt_convert` — generic naive-datetime converter (core primitive)
- [x] `dt_reprostim_to_utc` / `dt_bids_to_utc`
- [x] `dt_utc_to_reprostim` / `dt_utc_to_bids`
- [x] `dt_reprostim_to_bids` / `dt_bids_to_reprostim`
- [x] `dt_tz_label` — UTC offset string for display (e.g. `UTC-05:00`)
- [x] `dt_parse_dicom_time` / `dt_time_to_sec`
- [x] Apply timezone conversion in `_calc_scan_start_end_ts`

### Video matching and injection
- [x] Match scan window `[acq_time, acq_time + duration]` against video time range
- [x] Warn and skip when no video matches
- [x] Error and skip when multiple videos overlap (ambiguous match)
- [x] `nearby` layout: output next to NIfTI in same datatype folder
- [x] `top-stimuli` layout: output under `<bids_root>/stimuli/` mirroring hierarchy
- [x] `_find_bids_root` — walk up for `dataset_description.json`; fallback to `sub-` component
- [x] ReproIn `__dup-XX` suffix preserved in output filename
- [x] Media suffix determination (`_video` / `_audio` / `_audiovideo`) from `videos.tsv`
- [x] Delegate to `split-video` Python API (`do_main`)

### Dry-run mode
- [x] Skip `split-video` call and file writes when `--dry-run`
- [ ] Structured per-scan summary printed to stdout (onset, duration, buffers, paths)
- [ ] Final `[DRY-RUN] N injected, M skipped, K errors` summary line

### Summary / reporting
- [ ] Count injected / skipped / error records per run
- [ ] Print final `N injected, M skipped, K errors` summary line
- [ ] Non-zero exit code on errors

---

## Outputs

### A) Media file (`.mkv`) — BEP044:Stimuli
- [x] Output filename derived from NIfTI basename + `_recording-reprostim_<suffix>`
- [x] Output directory created if missing

### B) Sidecar JSON — BEP047:Behavior
- [x] Write `_recording-reprostim_<suffix>.json` alongside the `.mkv`
- [x] Include onset, duration, actual buffer values, etc
- [ ] Confirm field names against BEP044/BEP047 schema

### C) QR codes file — BIDS events-like `.tsv`
- [ ] Write `_recording-reprostim_events.tsv` (or finalised suffix) when QR data available
- [ ] Finalise suffix name (`_qrcodes` / `_codes` / `_qr` / `_qrinfo`)
- [ ] Columns: `onset`, `duration`, plus QR-derived fields

---

## QR Modes

- [ ] `none` — default, already working (no-op)
- [ ] `auto` — use JSONL if present alongside video, else skip refinement
- [ ] `embed-existing` — load pre-parsed QR JSONL; error if missing
- [ ] `parse` — invoke `qr-parse` on-the-fly on source video, then load results
- [ ] Apply QR-derived timing offset to `start / duration`

---

## Documentation

- [x] `split-video` added to RTD CLI index (`docs/source/cli/split-video.rst`)
- [x] `split-video` added to RTD API reference (`docs/source/api/index.rst`)
- [x] `bids-inject` listed in RTD CLI index
- [x] Spec: `--lock` section
- [x] Spec: Layout Modes section
- [x] Spec: Timezone Handling section with full `dt_` API

---

## Tests and Code Coverage

Test file location: `tests/qr/test_bids_inject.py` (to be created; mirrors `tests/audio/test_audiocodes.py` pattern).

### Datetime / Timezone API (`dt_` functions)

- [ ] `dt_resolve_tz("local")` → returns a valid `tzinfo`
- [ ] `dt_resolve_tz("UTC")` → `ZoneInfo("UTC")`
- [ ] `dt_resolve_tz("America/New_York")` → correct IANA zone
- [ ] `dt_resolve_tz("invalid/Zone")` → raises `ZoneInfoNotFoundError`
- [ ] `dt_resolve_tz` caching — same object returned on repeated calls with same name
- [ ] `dt_parse_bids` — naive ISO string → naive `datetime`
- [ ] `dt_parse_bids` — ISO string with UTC offset → strip `tzinfo`, return naive
- [ ] `dt_parse_bids` — invalid string → raises `ValueError`
- [ ] `dt_tz_label` — format is `UTC±HH:MM`
- [ ] `dt_tz_label("UTC")` → `UTC+00:00`
- [ ] `dt_convert` — round-trip: `convert(dt, tz_a, tz_b)` then back equals original
- [ ] `dt_reprostim_to_utc` — US Eastern naive → UTC naive (known offset)
- [ ] `dt_bids_to_utc` — same as above (independent function)
- [ ] `dt_utc_to_reprostim` — inverse of `dt_reprostim_to_utc`
- [ ] `dt_utc_to_bids` — inverse of `dt_bids_to_utc`
- [ ] `dt_reprostim_to_bids` — same TZ: identity; different TZ: correct shift
- [ ] `dt_bids_to_reprostim` — inverse of `dt_reprostim_to_bids`
- [ ] `dt_parse_dicom_time` — full format `HHMMSS.FFFFFF`
- [ ] `dt_parse_dicom_time` — short format `HHMMSS` (no fractional seconds)
- [ ] `dt_parse_dicom_time` — leap second `SS=60` clamped to `59`
- [ ] `dt_parse_dicom_time` — invalid format → raises `ValueError`
- [ ] `dt_time_to_sec` — midnight → `0.0`
- [ ] `dt_time_to_sec` — known time → correct total seconds incl. microseconds

### Internal helpers

- [ ] `_calc_bids_output_stem` — standard BIDS name (e.g. `_bold.nii.gz`) → correct stem, empty reproin suffix
- [ ] `_calc_bids_output_stem` — ReproIn `__dup-01` suffix → extracted correctly
- [ ] `_calc_bids_output_stem` — `.nii` (non-gzipped) → correct stem
- [ ] `_calc_media_suffix` — video only → `_video`
- [ ] `_calc_media_suffix` — audio only → `_audio`
- [ ] `_calc_media_suffix` — both → `_audiovideo`
- [ ] `_calc_media_suffix` — neither → `None`
- [ ] `_calc_scan_duration_sec` — Priority 1: `FrameAcquisitionDuration` (ms → sec)
- [ ] `_calc_scan_duration_sec` — Priority 2: `AcquisitionTime` array (2+ elements)
- [ ] `_calc_scan_duration_sec` — Priority 2: `AcquisitionTime` with single element → falls through
- [ ] `_calc_scan_duration_sec` — Priority 3: `RepetitionTime × NumberOfVolumes`
- [ ] `_calc_scan_duration_sec` — no metadata → `None`
- [ ] `_calc_scan_start_end_ts` — basic: `acq_time` + `duration_sec` → correct `(start, end)`
- [ ] `_calc_scan_start_end_ts` — `time_offset` applied correctly
- [ ] `_calc_scan_start_end_ts` — timezone conversion: BIDS UTC → ReproStim Eastern shifts time
- [ ] `_calc_scan_start_end_ts` — `duration_sec = None` → returns `None`
- [ ] `_find_bids_root` — `dataset_description.json` found by walking up
- [ ] `_find_bids_root` — fallback: parent of first `sub-` path component
- [ ] `_is_scans_file` — `*_scans.tsv` existing file → `True`
- [ ] `_is_scans_file` — directory or non-matching name → `False`

### Integration tests (with synthetic BIDS fixture)

> Requires a small synthetic BIDS dataset fixture (a few `_scans.tsv` files, stub JSON
> sidecars, and a stub `videos.tsv`) committed under `tests/data/bids_inject/`.

- [ ] Single `_scans.tsv` + matching video → `split-video` called with correct args (mocked)
- [ ] Dry-run: `split-video` not called; planned actions logged
- [ ] No matching video → scan skipped; no error raised
- [ ] Ambiguous match (2 videos overlap) → error logged, scan skipped
- [ ] `--match 'func/.*'` → only functional scans processed
- [ ] `--recursive` → all `_scans.tsv` files under directory tree processed
- [ ] `nearby` layout → output path is beside NIfTI
- [ ] `top-stimuli` layout → output path is under `stimuli/`
- [ ] ReproIn `__dup-01` filename → suffix preserved in output `.mkv` name
- [ ] `--lock no` → `FileLock` not acquired (mock / spy on `_get_tsv_records`)
- [ ] `--reprostim-timezone` / `--bids-timezone` → passed into `BiContext` correctly
- [ ] Mixed timezone scenario: Eastern ReproStim + UTC BIDS → times align after conversion

### CLI tests (Click `CliRunner`)

- [ ] `--help` renders without error
- [ ] Missing `--videos` → non-zero exit with error message
- [ ] Missing `PATHS` → non-zero exit with error message
- [ ] `--lock yes` / `--lock no` → converted to `bool` correctly in `do_main`
- [ ] `--reprostim-timezone America/New_York` passed through to `do_main`
- [ ] `--bids-timezone UTC` passed through to `do_main`
- [ ] Unknown `--layout` value → Click error (invalid choice)

### Coverage targets

| Module | Target |
|---|---|
| `qr/bids_inject.py` — `dt_` API functions | 100% |
| `qr/bids_inject.py` — internal helpers | ≥ 90% |
| `qr/bids_inject.py` — overall | ≥ 80% |
| `cli/cmd_bids_inject.py` | ≥ 80% |

### Test infrastructure

- [ ] Create `tests/qr/` package (`__init__.py`)
- [ ] Create `tests/qr/test_bids_inject.py`
- [ ] Create synthetic BIDS fixture under `tests/data/bids_inject/`
  - [ ] `dataset_description.json`
  - [ ] `sub-qa/ses-20250814/sub-qa_ses-20250814_scans.tsv` (2–3 rows)
  - [ ] Stub JSON sidecars for each scan row
  - [ ] Stub `videos.tsv` with matching time ranges
- [ ] Configure `pytest-cov` in `pyproject.toml` (or `setup.cfg`) with coverage report
- [ ] Add coverage badge / report to CI if not already present

---

## Open Questions / Future Work

- [ ] **Multi-video case** — scan spanning two capture files; currently errors (issue #14)
- [ ] **QR-sync / `bids-qr-sync`** — future tool; `--qr` modes lay the groundwork
- [ ] **Anonymized datasets** — `--time-offset` is manual; needs calibration workflow
- [ ] **DataLad integration** — auto-add output `.mkv` to BIDS DataLad dataset
- [ ] **Testing** — test datasets with known video-scan alignments
- [ ] **Strict Timing Mode** — integrate `tmaps` / `reproflow-data-sync` calibration data
- [ ] **Parallel processing** — `--jobs` option; lock protection for shared counters
- [ ] **con/duct integration**
- [ ] **`--skip` error policy** — e.g. `--skip=absent-video,unknown-timing,...`
- [ ] **`--duration` override** — manual scan duration for edge cases
