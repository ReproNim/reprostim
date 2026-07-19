# `video-audit` Task List

Tracks implementation progress against [audit-spec.md](audit-spec.md).

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
- [x] Extract recorded resolution/FPS/duration via `parse.do_info_file`
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

### Non-existing video handling (issue #253)
- [x] CLI `PATHS` argument accepts non-existent paths (removed `exists=True`)
- [x] CLI handler: for `rerun-for-na`/`reset-to-na`, non-existent paths emit warning instead of error
- [x] `do_main`: for `rerun-for-na`/`reset-to-na`, non-existent paths emit warning and continue instead of returning 1
- [x] `do_ext`: non-existent paths added to filter sets by extension heuristic (`.mkv`/`.mp4`/`.avi` → `path_files`, otherwise → `path_dirs`)
- [x] `run_ext_nosignal`: video file not on disk → set `no_signal_frames = "-3"`, update timestamp, increment counter
- [x] `run_ext_qr`: video file not on disk → set `qr_records_number = "-3"`, update timestamp, increment counter

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
- [x] `AudioInfo` — Pydantic model for audio stream info (codec, codec_long, codec_rfc6381, profile, sample_rate, channels, bits_per_sample, duration_sec, start_time, tag_str)
- [x] `VideoInfo` — Pydantic model for video stream info (codec, codec_long, codec_rfc6381, profile, level, width, height, pix_fmt, bit_depth, fps, duration_sec, start_time, tag_str)
- [x] `audio_codec_to_rfc6381` — RFC 6381 string for audio codec
- [x] `video_codec_to_rfc6381` — RFC 6381 string for video codec
- [x] `get_audio_video_info_ffprobe` — single ffprobe call returning `Tuple[AudioInfo, VideoInfo]`
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
- [x] `parse_audio_sr` — parse a composite `'48000Hz 16b 2ch aac'`-style string (the format
      `do_audit_file` assembles for `VaRecord.audio_sr`) into typed-ish string fields
      (`audio_sample_rate`/`audio_bit_depth`/`audio_channel_count`/`audio_codec`, `"n/a"` when
      absent). Moved here (public) from `video/split.py::_parse_audio_info` (private, same
      implementation) so both `video/split.py` and `bids/properties.py`
      (`bids_properties_from_video_audit`) can share one implementation instead of duplicating it
      — see [../bids/properties-spec.md](../bids/properties-spec.md). Tests moved from
      `tests/video/test_split.py` to `tests/video/test_audit.py` accordingly.

---

## Documentation

- [x] `video-audit` listed in RTD CLI index
- [ ] `video-audit` RST reference page with full option descriptions
- [ ] `VaContext` / `VaRecord` added to RTD API reference

---

## Tests and Code Coverage

Test file location: `tests/video/test_audit.py`

### Unit tests

#### Format utilities
- [x] `format_duration` — zero, sub-minute, hours, `None` → `"n/a"`
- [x] `format_date` — known datetime → `"YYYY-MM-DD"`, `None` → `"n/a"`
- [x] `format_time` — known datetime → `"HH:MM:SS.mmm"`, `None` → `"n/a"`

#### `parse_audio_sr`
- [x] Full string (`"48000Hz 16b 2ch aac"`) — all four fields parsed correctly
- [x] Missing bit depth — defaults `audio_bit_depth` to `"16"`
- [x] `None` input → all `"n/a"`
- [x] `"n/a"` string input → all `"n/a"`
- [x] Empty string input → all `"n/a"`
- [x] Sample-rate-only string → sample rate set, bit depth defaults to `"16"`, others `"n/a"`

(Moved verbatim from `tests/video/test_split.py`'s `_parse_audio_info` tests, renamed
`test_parse_audio_info_*` → `test_parse_audio_sr_*`, when the function itself moved — see
[../bids/properties-spec.md](../bids/properties-spec.md) Layering section.)

#### `check_coherent`
- [x] All fields valid and matching → `True`
- [x] `present=False` → `False`
- [x] `complete=False` → `False`
- [x] Missing start / end date-time → `False`
- [x] Missing detected or recorded res/fps → `False`
- [x] Resolution mismatch (detected ≠ recorded) → `False`
- [x] FPS mismatch (detected ≠ recorded) → `False`

#### `check_ffprobe`
- [x] `ffprobe` available (subprocess mock) → `True`
- [x] `ffprobe` not found (`FileNotFoundError` mock) → `False`

#### `audio_codec_to_rfc6381`
- [x] AAC LC → `"mp4a.40.2"`
- [x] AAC HE-AAC → `"mp4a.40.5"`
- [x] AAC unknown/None profile → defaults to `"mp4a.40.2"`
- [x] MP3 → `"mp4a.69"`
- [x] Opus → `"opus"`
- [x] Unknown codec → `None`

#### `video_codec_to_rfc6381`
- [x] H.264 High@L4.2 → `"avc1.64002A"`
- [x] H.264 Baseline@L3.0 → `"avc1.42001E"`
- [x] H.264 None level → `"avc1.4D0000"`
- [x] Unknown codec → `None`

#### `get_audio_video_info_ffprobe` (replaces `get_audio_info_ffprobe`)
- [x] Success — audio fields: codec/codec_long/profile/sample_rate/channels/start_time/tag_str/codec_rfc6381/duration set
- [x] Success — video fields: codec/codec_long/profile/level/width/height/pix_fmt/bit_depth/fps/codec_rfc6381/duration/start_time/tag_str set
- [x] Duration read from stream `duration` field (no DURATION tag)
- [x] No audio streams → AudioInfo all `None`, VideoInfo populated
- [x] `FileNotFoundError` → returns empty AudioInfo and VideoInfo
- [x] `CalledProcessError` → returns empty AudioInfo and VideoInfo

#### `_compare_rec_ts`
- [x] Both `n/a` → `0`
- [x] Equal timestamps → `0`
- [x] Left `n/a`, right valid → `-1`
- [x] Right `n/a`, left valid → `1`
- [x] Left earlier → `-1`, left later → `1`

#### `_match_recs`
- [x] Identical lists → `True`
- [x] Different length → `False`
- [x] Same length, different content → `False`

#### `_merge_rec`
- [x] All timestamps equal → returns `rec_new`
- [x] Newer internal in `rec_new` → internal fields from `rec_new`
- [x] Newer nosignal in `rec_cur` → nosignal fields from `rec_cur`
- [x] Newer QR in `rec_new` → qr fields from `rec_new`
- [x] Name mismatch → `ValueError` raised

#### `_merge_recs`
- [x] `full` mode → `rec_new` overrides everything
- [x] `force` mode → new records merged over existing
- [x] `force` mode with empty `recs_cur` → returns `recs_new` directly
- [x] `incremental` mode → timestamp-based selective merge
- [x] `incremental` mode → brand-new record added alongside existing
- [x] `rerun-for-na` mode → timestamp-based selective merge
- [x] No change in `recs_cur` → merge skipped

#### TSV I/O
- [x] `_save_tsv` / `_load_tsv` round-trip with temp file
- [x] `_save_tsv` writes LF-only line endings (no CRLF / `^M`) on all platforms
- [x] `_load_tsv` reads file with LF line endings correctly
- [x] `_load_tsv` reads file with CRLF line endings correctly (no `\r` in field values)
- [x] `_get_tsv_records` — with lock (default)
- [x] `_get_tsv_records` — cached=True returns cached list on second call
- [x] `_get_tsv_records` — use_lock=False dirty-read

#### Metadata log parsing
- [x] `iter_metadata_json` — valid JSON lines yielded
- [x] `iter_metadata_json` — missing log file → empty generator
- [x] `iter_metadata_json` — invalid JSON in line → silently skipped
- [x] `find_metadata_json` — matching entry found
- [x] `find_metadata_json` — no matching entry → `None`

#### `_parse_rec_datetime`
- [x] Valid date + time strings → `datetime` object
- [x] Either value is `"n/a"` → `None`
- [x] Malformed strings → `None` (ValueError path)

#### `find_video_audit_by_timerange`
- [x] Record intersects range → included in result
- [x] Record entirely before range → excluded
- [x] Record entirely after range → excluded
- [x] Records sorted by start time ascending
- [x] `present=False` → excluded
- [x] `complete=False` → excluded
- [x] `start_date="n/a"` → excluded
- [x] `end_date="n/a"` → excluded

#### Path and context helpers
- [x] `_build_dated_path` — with valid `start_date` → dated subdirectory created
- [x] `_build_dated_path` — `start_date="n/a"` → file placed in base dir

#### `do_audit_file`
- [x] Happy path (all mocked): present file, session_begin metadata, full vi/vti/audio → coherent VaRecord yielded
- [x] File does not exist → VaRecord with `present=False` yielded
- [x] `max_counter` reached → nothing yielded
- [x] `skip_names` match by full path → nothing yielded
- [x] `skip_names` match by base name (after existence check) → nothing yielded
- [x] `path_mask` no-match → nothing yielded

#### `do_audit_dir` / `do_audit_internal`
- [x] `do_audit_dir` — directory with .mkv files → records yielded
- [x] `do_audit_dir` — missing path → nothing yielded
- [x] `do_audit_dir` — non-directory path → nothing yielded
- [x] `do_audit_dir` — `max_counter` reached → nothing yielded
- [x] `do_audit_dir` — recursive descent into subdirectory
- [x] `do_audit_internal` — skipped for `rerun-for-na` mode
- [x] `do_audit_internal` — skipped for `reset-to-na` mode
- [x] `do_audit_internal` — skipped for non-INTERNAL source
- [x] `do_audit_internal` — single file path → delegates to `do_audit_file`
- [x] `do_audit_internal` — directory path → delegates to `do_audit_dir`
- [x] `do_audit_internal` — non-existent path → nothing yielded

#### External tool early-exit paths
- [x] `run_ext_nosignal` — source not NOSIGNAL/ALL → returns `vr` unchanged
- [x] `run_ext_nosignal` — `reset-to-na` mode → `no_signal_frames` set to `"n/a"`
- [x] `run_ext_nosignal` — `reset-to-na` already `n/a` → counter not incremented
- [x] `run_ext_nosignal` — `rerun-for-na` + non-`n/a` → skipped
- [x] `run_ext_nosignal` — `max_counter` reached → returns `vr` unchanged
- [x] `run_ext_nosignal` — `path_mask` no-match → returns `vr` unchanged
- [x] `run_ext_nosignal` — video file not on disk → `no_signal_frames = "-3"`, timestamp updated
- [x] `run_ext_nosignal` — video file not on disk in `rerun-for-na` → sentinel `-3` breaks retry loop
- [x] `run_ext_nosignal` — subprocess success with `nosignal_rate` → percentage stored
- [x] `run_ext_nosignal` — subprocess success without `nosignal_rate` key → `"0.0"`
- [x] `run_ext_nosignal` — `CalledProcessError` → `no_signal_frames` unchanged
- [x] `run_ext_qr` — source not QR/ALL → returns `vr` unchanged
- [x] `run_ext_qr` — `reset-to-na` mode → `qr_records_number` set to `"n/a"`
- [x] `run_ext_qr` — `reset-to-na` already `n/a` → counter not incremented
- [x] `run_ext_qr` — `rerun-for-na` + non-`n/a` → skipped
- [x] `run_ext_qr` — `max_counter` reached → returns `vr` unchanged
- [x] `run_ext_qr` — `path_mask` no-match → returns `vr` unchanged
- [x] `run_ext_qr` — video file not on disk → `qr_records_number = "-3"`, timestamp updated
- [x] `run_ext_qr` — video file not on disk in `rerun-for-na` → sentinel `-3` breaks retry loop
- [x] `run_ext_qr` — subprocess success with `ParseSummary` → `qr_count` stored
- [x] `run_ext_qr` — ffmpeg `CalledProcessError` → `qr_records_number` = `"-2"`
- [x] `run_ext_qr` — no `ParseSummary` in output → `qr_records_number` = `"-1"`
- [x] `run_ext_all` — delegates to nosignal then qr
- [x] `do_audit` — delegates to `do_audit_internal` + `run_ext_all`

#### `do_ext`
- [x] Empty path list → all records processed
- [x] `["*"]` path list → all records processed
- [x] Record path matches explicit file → processed
- [x] Record path starts with directory → processed
- [x] Record not matching filter → yielded unchanged
- [x] Non-existent `.mkv` path → added to `path_files` filter (matches record by string)
- [x] Non-existent non-video path → added to `path_dirs` filter (matches record by prefix)

#### `do_main`
- [x] Invalid path → returns `1`
- [x] Incremental mode, no existing TSV → creates new TSV, returns `0`
- [x] Incremental mode, existing TSV → loads existing, merges, saves
- [x] `rerun-for-na` mode → calls `do_ext` on existing records
- [x] `rerun-for-na` mode + non-existent path → warns and returns `0` (not `1`)
- [x] `reset-to-na` mode + non-existent path → warns and returns `0` (not `1`)
- [x] `incremental` mode + non-existent path → returns `1` (unchanged behavior)
- [x] `nosignal_opts` / `qr_opts` strings shlex-parsed into `VaContext`
- [x] `ffprobe` missing → prints error message, still returns `0`
- [x] `verbose=True` → records printed as JSON via `out_func`

#### `get_file_video_audit`
- [x] TSV exists and contains matching path → returns cached record
- [x] TSV missing match → falls back to live `do_audit_file`
- [x] `Timeout` while acquiring lock → falls back to `do_audit_file`
- [x] Generic exception loading TSV → falls back to `do_audit_file`

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
- [x] Config `audit-src` as scalar string → wrapped in tuple
- [x] `--mode full` → `VaMode.FULL` passed to `do_main`
- [x] Unknown `--mode` value → Click error

### Coverage targets

| Module | Target | Current |
|---|---|---|
| `video/audit.py` — overall | ≥ 80% | 93% |
| `cli/cmd_video_audit.py` | ≥ 80% | 94% |

_Updated for issue #253: 12 new tests added (164 total), covering non-existing video handling for all 3 audit sources and CLI layer._

---

## Open Questions / Future Work

- [ ] **Parallel processing** — `--jobs` option for concurrent file processing
- [x] **`-c / --config` YAML support** — implemented
- [ ] **Progress reporting** — tqdm progress bar for large directories
- [ ] **`--columns` filter** — select which TSV columns to populate
- [ ] **DataLad integration** — auto-`datalad save` after TSV update
