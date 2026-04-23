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

- [ ] `format_duration` — zero, sub-minute, hours
- [ ] `format_date` / `format_time` — known datetime → expected string
- [ ] `check_coherent` — coherent record → `True`; missing fields → `False`
- [ ] `_compare_rec_ts` — `n/a` ordering, equal timestamps, earlier/later
- [ ] `_merge_rec` — internal/nosignal/qr timestamp priority
- [ ] `_merge_recs` — full / force / incremental / rerun-for-na modes
- [ ] `find_video_audit_by_timerange` — intersects, non-overlapping, boundary cases

### CLI tests (Click `CliRunner`)

- [x] `--help` renders without error
- [x] `--nosignal-opts` string parsed and forwarded to `VaContext.nosignal_opts`
- [x] `--qr-opts` string parsed and forwarded to `VaContext.qr_opts`
- [x] Omitting `--nosignal-opts` → `VaContext` uses built-in default
- [x] Omitting `--qr-opts` → `VaContext` uses built-in default
- [ ] `-c / --config` YAML loaded; config values used as defaults, CLI flags override
- [ ] Config key `nosignal-opts` forwarded to `VaContext.nosignal_opts`
- [ ] Config key `qr-opts` forwarded to `VaContext.qr_opts`
- [ ] Config keys for all other CLI options respected
- [ ] `--mode full` → `VaMode.FULL` passed to `do_main`
- [ ] Unknown `--mode` value → Click error

### Coverage targets

| Module | Target | Current |
|---|---|---|
| `qr/video_audit.py` — overall | ≥ 80% | 0% (pending) |
| `cli/cmd_video_audit.py` | ≥ 80% | 0% (pending) |

---

## Open Questions / Future Work

- [ ] **Parallel processing** — `--jobs` option for concurrent file processing
- [x] **`-c / --config` YAML support** — implemented
- [ ] **Progress reporting** — tqdm progress bar for large directories
- [ ] **`--columns` filter** — select which TSV columns to populate
- [ ] **DataLad integration** — auto-`datalad save` after TSV update
