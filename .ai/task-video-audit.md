# `video-audit` Task List

Tracks implementation progress against [spec-video-audit.md](spec-video-audit.md).

---

## CLI Options

- [x] `PATHS` argument — one or more video files or directories
- [x] `-m / --mode [full|incremental|force|rerun-for-na|reset-to-na]`
- [x] `-o / --output` — output TSV file (default: `videos.tsv`)
- [x] `-r / --recursive` — recursively scan subdirectories
- [x] `-s / --audit-src [internal|qr|nosignal|all]` — repeatable
- [x] `-l / --max-files` — limit number of records processed
- [x] `-p / --path-mask` — fnmatch-style filter on file paths
- [x] `-v / --verbose` — print JSON records to stdout
- [x] `-n / --nosignal-opts` — override detect-noscreen options (shlex string)
- [x] `-q / --qr-opts` — override qr-parse options (shlex string)
- [x] Add short forms `-n` and `-q` to existing `--nosignal-opts` / `--qr-opts` in CLI code
- [x] `-c / --config` — optional YAML config file with CLI-override precedence
- [x] Add `pyyaml>=6.0` to `pyproject.toml` dependencies

---

## Core Logic

### File discovery
- [x] Process a single video file directly
- [x] Scan a directory for `.mkv`, `.mp4`, `.avi` files
- [x] Recursive directory traversal (`--recursive`)
- [x] Mixed list of files and directories in a single invocation
- [x] fnmatch path mask filtering (`--path-mask`)
- [x] `skip_names` set to skip already-processed files in incremental mode

### Internal audit (`VaSource.INTERNAL`)
- [x] Extract start/end timestamps from `.log` sidecar
- [x] Extract video resolution and FPS from `session_begin` metadata
- [x] Extract recorded resolution/FPS/duration via `qr_parse.do_info_file`
- [x] Extract audio info (codec, sample rate, channels, duration) via ffprobe
- [x] Compute human-readable duration (`HH:MM:SS.mmm`)
- [x] Coherence check (`check_coherent`) — res/fps/timestamps consistent

### External audit — nosignal (`VaSource.NOSIGNAL`)
- [x] Run `reprostim detect-noscreen` on each video
- [x] Store JSON output under dated path in `nosignal_data_dir`
- [x] Store log output under dated path in `nosignal_log_dir`
- [x] Parse `nosignal_rate` from JSON and store as percentage
- [x] Per-file lock (`.nosignal.lock`) to prevent concurrent runs
- [x] Pass `nosignal_opts` to detect-noscreen via `VaContext`
- [x] Accept `--nosignal-opts` override from CLI (shlex-parsed)

### External audit — QR (`VaSource.QR`)
- [x] Convert video to audio-free copy via ffmpeg (temp dir)
- [x] Run `reprostim qr-parse` on temp copy
- [x] Store JSONL output under dated path in `qr_data_dir`
- [x] Store log output under dated path in `qr_log_dir`
- [x] Parse `ParseSummary.qr_count` from JSONL output
- [x] Per-file lock (`.qr.lock`) to prevent concurrent runs
- [x] Pass `qr_opts` to qr-parse via `VaContext`
- [x] Accept `--qr-opts` override from CLI (shlex-parsed)

### Operation modes (`VaMode`)
- [x] `full` — regenerate all records from scratch
- [x] `incremental` — process only new files, merge into existing TSV
- [x] `force` — redo/update existing records
- [x] `rerun-for-na` — rerun external tools only for records with `n/a` values
- [x] `reset-to-na` — reset external-tool fields to `n/a`

### TSV handling
- [x] Load existing `videos.tsv` with file lock
- [x] Save sorted records to `videos.tsv`
- [x] `_merge_recs` — timestamp-aware merge of old/current/new record sets
- [x] `_merge_rec` — per-record merge using `updated_on`, `no_signal_updated_on`, `qr_updated_on`
- [x] Module-level TSV cache (`_tsv_cache`) with `cached` / `use_lock` flags
- [x] `find_video_audit_by_timerange` — intersect-based lookup for BIDS injection

---

## API

- [x] `VaRecord` — Pydantic model for a single TSV row
- [x] `VaContext` — Pydantic model carrying all processing options
- [x] `VaMode` — enum of operation modes
- [x] `VaSource` — enum of audit sources
- [x] `do_audit_file` — audit a single video file (INTERNAL)
- [x] `do_audit_dir` — audit all videos in a directory
- [x] `do_audit_internal` — entry point for INTERNAL source
- [x] `run_ext_nosignal` — run detect-noscreen on a record
- [x] `run_ext_qr` — run qr-parse on a record
- [x] `run_ext_all` — run all external tools on a record
- [x] `do_audit` — full pipeline (internal + external)
- [x] `do_ext` — external-only pass over existing records
- [x] `do_main` — CLI entry point
- [x] `get_file_video_audit` — single-file lookup (TSV or live audit)
- [x] `find_video_audit_by_timerange` — time-range lookup for BIDS

---

## Documentation

- [x] `video-audit` listed in RTD CLI index
- [ ] `video-audit` RST reference page with full option descriptions
- [ ] `VaContext` / `VaRecord` added to RTD API reference

---

## Tests and Code Coverage

Test file location: `tests/qr/test_video_audit.py`

### Unit tests

#### Format utilities
- [ ] `format_duration` — zero, sub-minute, hours, `None` → `"n/a"`
- [ ] `format_date` — known datetime → `"YYYY-MM-DD"`, `None` → `"n/a"`
- [ ] `format_time` — known datetime → `"HH:MM:SS.mmm"`, `None` → `"n/a"`

#### `check_coherent`
- [ ] All fields valid and matching → `True`
- [ ] `present=False` → `False`
- [ ] `complete=False` → `False`
- [ ] Missing start / end date-time → `False`
- [ ] Missing detected or recorded res/fps → `False`
- [ ] Resolution mismatch (detected ≠ recorded) → `False`
- [ ] FPS mismatch (detected ≠ recorded) → `False`

#### `check_ffprobe`
- [ ] `ffprobe` available (subprocess mock) → `True`
- [ ] `ffprobe` not found (`FileNotFoundError` mock) → `False`

#### `_compare_rec_ts`
- [ ] Both `n/a` → `0`
- [ ] Equal timestamps → `0`
- [ ] Left `n/a`, right valid → `-1`
- [ ] Right `n/a`, left valid → `1`
- [ ] Left earlier → `-1`, left later → `1`

#### `_match_recs`
- [ ] Identical lists → `True`
- [ ] Different length → `False`
- [ ] Same length, different content → `False`

#### `_merge_rec`
- [ ] All timestamps equal → returns `rec_new`
- [ ] Newer internal in `rec_new` → internal fields from `rec_new`
- [ ] Newer nosignal in `rec_cur` → nosignal fields from `rec_cur`
- [ ] Newer QR in `rec_new` → qr fields from `rec_new`

#### `_merge_recs`
- [ ] `full` mode → `rec_new` overrides everything
- [ ] `force` mode → new records merged over existing
- [ ] `incremental` mode → timestamp-based selective merge
- [ ] `rerun-for-na` mode → timestamp-based selective merge
- [ ] No change in `recs_cur` → merge skipped

#### TSV I/O
- [ ] `_save_tsv` / `_load_tsv` round-trip with temp file
- [ ] `_get_tsv_records` — with lock (default)
- [ ] `_get_tsv_records` — cached=True returns cached list on second call
- [ ] `_get_tsv_records` — use_lock=False dirty-read

#### Metadata log parsing
- [ ] `iter_metadata_json` — valid JSON lines yielded
- [ ] `iter_metadata_json` — missing log file → empty generator
- [ ] `find_metadata_json` — matching entry found
- [ ] `find_metadata_json` — no matching entry → `None`

#### `_parse_rec_datetime`
- [ ] Valid date + time strings → `datetime` object
- [ ] Either value is `"n/a"` → `None`

#### `find_video_audit_by_timerange`
- [ ] Record intersects range → included in result
- [ ] Record entirely before range → excluded
- [ ] Record entirely after range → excluded
- [ ] Records sorted by start time ascending

#### Path and context helpers
- [ ] `_build_dated_path` — with valid `start_date` → dated subdirectory created
- [ ] `_build_dated_path` — `start_date="n/a"` → file placed in base dir

#### `do_audit_file`
- [ ] Happy path (all mocked): present file, session_begin metadata, full vi/vti/audio → coherent VaRecord yielded
- [ ] File does not exist → VaRecord with `present=False` yielded
- [ ] `max_counter` reached → nothing yielded
- [ ] `skip_names` match → nothing yielded
- [ ] `path_mask` no-match → nothing yielded

#### `do_audit_dir` / `do_audit_internal`
- [ ] `do_audit_dir` — directory with .mkv files → records yielded
- [ ] `do_audit_internal` — skipped for `rerun-for-na` mode
- [ ] `do_audit_internal` — skipped for `reset-to-na` mode

#### External tool early-exit paths
- [ ] `run_ext_nosignal` — source not NOSIGNAL/ALL → returns `vr` unchanged
- [ ] `run_ext_nosignal` — `reset-to-na` mode → `no_signal_frames` set to `"n/a"`
- [ ] `run_ext_nosignal` — `rerun-for-na` + non-`n/a` → skipped
- [ ] `run_ext_qr` — source not QR/ALL → returns `vr` unchanged
- [ ] `run_ext_qr` — `reset-to-na` mode → `qr_records_number` set to `"n/a"`
- [ ] `run_ext_qr` — `rerun-for-na` + non-`n/a` → skipped

#### `do_main`
- [ ] Invalid path → returns `1`
- [ ] Incremental mode, no existing TSV → creates new TSV, returns `0`
- [ ] Incremental mode, existing TSV → loads existing, merges, saves
- [ ] `rerun-for-na` mode → calls `do_ext` on existing records
- [ ] `nosignal_opts` / `qr_opts` strings shlex-parsed into `VaContext`

#### `get_file_video_audit`
- [ ] TSV exists and contains matching path → returns cached record
- [ ] TSV missing match → falls back to live `do_audit_file`

### CLI tests (Click `CliRunner`)

- [x] `--help` renders without error
- [x] `--nosignal-opts` string parsed and forwarded to `VaContext.nosignal_opts`
- [x] `--qr-opts` string parsed and forwarded to `VaContext.qr_opts`
- [x] Omitting `--nosignal-opts` → `VaContext` uses built-in default
- [x] Omitting `--qr-opts` → `VaContext` uses built-in default
- [x] `-c / --config` YAML loaded; config values used as defaults, CLI flags override
- [x] Config key `nosignal-opts` forwarded to `VaContext.nosignal_opts`
- [x] Config key `qr-opts` forwarded to `VaContext.qr_opts`
- [x] Config keys for all other CLI options respected
- [ ] Config `audit-src` as scalar string → wrapped in tuple
- [ ] `--mode full` → `VaMode.FULL` passed to `do_main`
- [ ] Unknown `--mode` value → Click error

### Coverage targets

| Module | Target | Current |
|---|---|---|
| `qr/video_audit.py` — overall | ≥ 80% | 14% |
| `cli/cmd_video_audit.py` | ≥ 80% | 92% |

---

## Open Questions / Future Work

- [ ] **Parallel processing** — `--jobs` option for concurrent file processing
- [x] **`-c / --config` YAML support** — implemented
- [ ] **Progress reporting** — tqdm progress bar for large directories
- [ ] **`--columns` filter** — select which TSV columns to populate
- [ ] **DataLad integration** — auto-`datalad save` after TSV update
