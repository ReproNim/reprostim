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
- [x] `-q / --qr [none|auto|embed-existing|parse]` — option defined; logic not yet implemented
- [x] `-l / --layout [nearby|top-stimuli]`
- [x] `-z / --reprostim-timezone` — timezone for `videos.tsv` timestamps
- [x] `-Z / --bids-timezone` — timezone for BIDS `acq_time` values
- [x] `-m / --match REGEX` — filter scan records by filename
- [x] `-d / --dry-run`
- [x] `-w / --overwrite [skip|force|always|error]` — policy for existing output files
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

### ScanMetadata model
- [x] `TaskName` — parsed from BIDS JSON sidecar; `None` when absent; excluded from `extra`
- [x] `FrameAcquisitionDuration`, `AcquisitionTime`, `RepetitionTime`, `NumberOfVolumes` — existing typed fields

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
- [x] Build `sidecar_metadata` dict from `record.metadata.TaskName` and pass to `do_main`

### Dry-run mode
- [x] Skip `split-video` call and file writes when `--dry-run`
- [x] Structured per-scan summary printed to stdout (onset, duration, buffers, paths)
- [x] Final `[DRY-RUN] N injected, M skipped, K errors` summary line

### Overwrite mode
- [x] `OverwriteMode` enum (`skip` / `force` / `always` / `error`)
- [x] Check both output `.mkv` and sidecar `.json` for existence (including symlinks)
- [x] `skip` — existing output → log info, count as skipped, return early
- [x] `force` — existing output → `os.remove()` both files, then re-inject (handles git-annex read-only symlinks)
- [x] `always` — no existence check, run `split-video` as-is (pre-feature behaviour)
- [x] `error` — existing output → log error, append to `summary.errors`, count as error

### Summary / reporting
- [x] Count processed / injected / skipped / error records per run
- [x] Print final `N processed, N injected, M skipped, K errors` summary line
- [x] In verbose mode, print numbered error list after summary
- [x] Non-zero exit code on errors
- [x] Capture `ERROR:` lines from `split-video` `out_func` for detailed error summary

---

## Outputs

### A) Media file (`.mkv`) — BEP044:Stimuli
- [x] Output filename derived from NIfTI basename + `_recording-reprostim_<suffix>`
- [x] Output directory created if missing

### B) Sidecar JSON — BEP047:Behavior
- [x] Write `_recording-reprostim_<suffix>.json` alongside the `.mkv`
- [x] Include onset, duration, actual buffer values, etc
- [x] `RecordingDuration` maps from `SplitResult.buffer_duration` (total file duration with buffers)
- [ ] Confirm field names against BEP044/BEP047 schema

### C) QR codes file — BIDS events-like `.tsv`
- [ ] Write `_recording-reprostim_events.tsv` (or finalised suffix) when QR data available
- [ ] Finalise suffix name (`_qrcodes` / `_codes` / `_qr` / `_qrinfo`)
- [ ] Columns: `onset`, `duration`, plus QR-derived fields

### D) _scans.tsv annotation — `reprostim_*` columns
- [ ] Add `ScansModel` / `ScanRecord` fields for the four annotation columns
- [ ] Write-back `reprostim_buffer_before`, `reprostim_buffer_after`, `reprostim_path`, `reprostim_offset` to `_scans.tsv` after successful injection
- [ ] Rows that are skipped or error → write `n/a` for all four columns (when column is newly added to file)
- [ ] Preserve all existing columns; append new ones to the right
- [ ] Handle re-runs: update existing `reprostim_*` columns in-place (don't duplicate)
- [ ] Skip write-back in `--dry-run` mode
- [ ] `reprostim_path` stored relative to `videos.tsv` location (consistent with `videos.tsv` path convention)

---

## QR Modes

- [x] `none` — default, already working (no-op)
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
- [x] Spec: Overwrite Mode section (all 4 modes, git-annex interaction)

---

## Tests and Code Coverage

Test file location: `tests/qr/test_bids_inject.py` (mirrors `tests/audio/test_audiocodes.py` pattern).

### Datetime / Timezone API (`dt_` functions)

- [x] `dt_resolve_tz("local")` → returns a valid `tzinfo`
- [x] `dt_resolve_tz("UTC")` → `ZoneInfo("UTC")`
- [x] `dt_resolve_tz("America/New_York")` → correct IANA zone
- [x] `dt_resolve_tz("invalid/Zone")` → raises `ZoneInfoNotFoundError`
- [x] `dt_resolve_tz` caching — same object returned on repeated calls with same name
- [x] `dt_parse_bids` — naive ISO string → naive `datetime`
- [x] `dt_parse_bids` — ISO string with UTC offset → strip `tzinfo`, return naive
- [x] `dt_parse_bids` — invalid string → raises `ValueError`
- [x] `dt_tz_label` — format is `UTC±HH:MM`
- [x] `dt_tz_label("UTC")` → `UTC+00:00`
- [x] `dt_convert` — round-trip: `convert(dt, tz_a, tz_b)` then back equals original
- [x] `dt_reprostim_to_utc` — US Eastern naive → UTC naive (known offset)
- [x] `dt_bids_to_utc` — same as above (independent function)
- [x] `dt_utc_to_reprostim` — inverse of `dt_reprostim_to_utc`
- [x] `dt_utc_to_bids` — inverse of `dt_bids_to_utc`
- [x] `dt_reprostim_to_bids` — same TZ: identity; different TZ: correct shift
- [x] `dt_bids_to_reprostim` — inverse of `dt_reprostim_to_bids`
- [x] `dt_parse_dicom_time` — full format `HHMMSS.FFFFFF`
- [x] `dt_parse_dicom_time` — short format `HHMMSS` (no fractional seconds)
- [x] `dt_parse_dicom_time` — leap second `SS=60` clamped to `59`
- [x] `dt_parse_dicom_time` — invalid format → raises `ValueError`
- [x] `dt_time_to_sec` — midnight → `0.0`
- [x] `dt_time_to_sec` — known time → correct total seconds incl. microseconds

### Internal helpers

- [x] `_calc_bids_output_stem` — standard BIDS name (e.g. `_bold.nii.gz`) → correct stem, empty reproin suffix
- [x] `_calc_bids_output_stem` — ReproIn `__dup-01` suffix → extracted correctly
- [x] `_calc_bids_output_stem` — `.nii` (non-gzipped) → correct stem
- [x] `_calc_media_suffix` — video only → `_video`
- [x] `_calc_media_suffix` — audio only → `_audio`
- [x] `_calc_media_suffix` — both → `_audiovideo`
- [x] `_calc_media_suffix` — neither → `None`
- [x] `ScanMetadata.TaskName` — defaults to `None`
- [x] `ScanMetadata.TaskName` — stores task name string when set
- [x] `_parse_scan_metadata` — reads `TaskName` from JSON sidecar when present
- [x] `_parse_scan_metadata` — `TaskName` is `None` when key absent from sidecar
- [x] `_parse_scan_metadata` — `TaskName` is NOT stored in `extra` (it is a known key)
- [x] `_calc_scan_duration_sec` — Priority 1: `FrameAcquisitionDuration` (ms → sec)
- [x] `_calc_scan_duration_sec` — Priority 2: `AcquisitionTime` array (2+ elements)
- [x] `_calc_scan_duration_sec` — Priority 2: `AcquisitionTime` with single element → falls through
- [x] `_calc_scan_duration_sec` — Priority 3: `RepetitionTime × NumberOfVolumes`
- [x] `_calc_scan_duration_sec` — no metadata → `None`
- [x] `_calc_scan_start_end_ts` — basic: `acq_time` + `duration_sec` → correct `(start, end)`
- [x] `_calc_scan_start_end_ts` — `time_offset` applied correctly
- [x] `_calc_scan_start_end_ts` — timezone conversion: BIDS UTC → ReproStim Eastern shifts time
- [x] `_calc_scan_start_end_ts` — `duration_sec = None` → returns `None`
- [x] `_find_bids_root` — `dataset_description.json` found by walking up
- [x] `_find_bids_root` — fallback: parent of first `sub-` path component
- [x] `_is_scans_file` — `*_scans.tsv` existing file → `True`
- [x] `_is_scans_file` — directory or non-matching name → `False`

### Integration tests (with synthetic BIDS fixture)

> Requires a small synthetic BIDS dataset fixture (a few `_scans.tsv` files, stub JSON
> sidecars, and a stub `videos.tsv`) committed under `tests/data/bids_inject/`.

- [ ] Single `_scans.tsv` + matching video → `split-video` called with correct args (mocked)
- [x] Dry-run: `split-video` not called; planned actions logged
- [x] No matching video → scan skipped; no error raised
- [x] Ambiguous match (2 videos overlap) → error logged with scan window + matched video list
- [x] `--match 'func/.*'` → only functional scans processed
- [ ] `--recursive` → all `_scans.tsv` files under directory tree processed
- [ ] `nearby` layout → output path is beside NIfTI
- [x] `top-stimuli` layout → output path is under `stimuli/`
- [x] ReproIn `__dup-01` filename → suffix preserved in output `.mkv` name
- [ ] `--lock no` → `FileLock` not acquired (mock / spy on `_get_tsv_records`)
- [ ] `--reprostim-timezone` / `--bids-timezone` → passed into `BiContext` correctly
- [ ] Mixed timezone scenario: Eastern ReproStim + UTC BIDS → times align after conversion

### _scans.tsv annotation tests

- [ ] Successful injection → all four `reprostim_*` columns written with correct values
- [ ] Skipped scan → four columns written as `n/a`
- [ ] Re-run (columns already present) → columns updated in-place, no duplication
- [ ] `--dry-run` → `_scans.tsv` not modified
- [ ] `reprostim_path` is relative to `videos.tsv` location, not absolute

### Overwrite mode tests

- [x] `skip` + existing output → 0 injected, files untouched, counted as skipped
- [x] `skip` + no existing output → 1 injected (normal path)
- [x] `force` + existing output → both `.mkv` and `.json` removed, 1 injected
- [x] `always` + existing output → 1 injected, files not pre-removed
- [x] `error` + existing output → exit 1, 1 error, error detail in verbose output
- [x] `error` + no existing output → 1 injected (normal path)

### sidecar_metadata propagation tests

- [x] `_call_split_video` passes `sidecar_metadata` with `TaskName` from `record.metadata` to `split-video` `do_main`
- [x] `_call_split_video` passes empty `sidecar_metadata` when `TaskName` is absent from sidecar JSON

### CLI tests (Click `CliRunner`)

- [ ] `--help` renders without error
- [ ] Missing `--videos` → non-zero exit with error message
- [ ] Missing `PATHS` → non-zero exit with error message
- [ ] `--lock yes` / `--lock no` → converted to `bool` correctly in `do_main`
- [ ] `--reprostim-timezone America/New_York` passed through to `do_main`
- [ ] `--bids-timezone UTC` passed through to `do_main`
- [ ] Unknown `--layout` value → Click error (invalid choice)

### Coverage targets

| Module | Target | Current |
|---|---|---|
| `qr/bids_inject.py` — `dt_` API functions | 100% | **100%** ✓ |
| `qr/bids_inject.py` — internal helpers | ≥ 90% | 0% (pending) |
| `qr/bids_inject.py` — overall | ≥ 80% | 34% (pending) |
| `cli/cmd_bids_inject.py` | ≥ 80% | 0% (pending) |

### Test infrastructure

- [x] Create `tests/qr/` package (`__init__.py`)
- [x] Create `tests/qr/test_bids_inject.py`
- [x] Create synthetic BIDS fixture under `tests/data/bids_inject/`
  - [x] `dataset_description.json`
  - [x] `sub-qa/ses-20250814/sub-qa_ses-20250814_scans.tsv` (2–3 rows)
  - [x] Stub JSON sidecars for each scan row
  - [ ] Stub `videos.tsv` with matching time ranges (generated per-test in `tmp_path`)
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
- [x] **`--overwrite` policy** — `-w / --overwrite [skip|force|always|error]` implemented for existing output file handling
- [ ] **`--duration` override** — manual scan duration for edge cases
