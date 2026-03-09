# `split-video` Task List

Tracks implementation progress against [spec-split-video.md](spec-split-video.md).

---

## CLI Options

- [x] `-i / --input` — path to input video file (required)
- [x] `-o / --output` — output `.mkv` file path (required; template when multiple `--spec`)
- [x] `--start` — start time (ISO 8601 datetime or time-only)
- [x] `--duration` — duration in seconds or ISO 8601 duration string
- [x] `--end` — end time (ISO 8601 datetime or time-only); mutually exclusive with `--duration`
- [x] `--buffer-before` — extra video before start time (seconds or ISO 8601)
- [x] `--buffer-after` — extra video after end time (seconds or ISO 8601)
- [x] `--buffer-policy [strict|flexible]` — error or trim when buffers exceed video boundaries
- [x] `--spec` — compact inline segment spec (`START/DURATION` or `START//END`); repeatable; mutually exclusive with `--start`/`--duration`/`--end`
- [x] `-j / --sidecar-json` — sidecar JSON output control (`none` / `auto` / explicit path)
- [x] `-a / --video-audit-file` — path to `videos.tsv` (optional, skips on-the-fly metadata)
- [x] `--raw` — raw mode: any video file accepted, no filename timestamp required
- [x] `-k / --lock [yes|no]` — advisory file lock for `videos.tsv`
- [x] `-v / --verbose` — verbose output

---

## Core Logic

### Input / timestamp parsing
- [x] `_parse_ts` — ISO 8601 datetime → `datetime`; time-only → offset from video start
- [x] `_parse_interval_sec` — seconds float or ISO 8601 duration → float seconds
- [x] `_parse_date_time` — `date_str` + `time_str` → naive `datetime`
- [x] `_parse_fps` — fps string → float
- [x] `_parse_audio_info` — audio info string → dict

### Spec parsing and output templates
- [x] `_parse_spec` — `START/DURATION` and `START//END` formats parsed to `SpecEntry`
- [x] `_expand_output_template` — `{n}`, `{start}`, `{end}`, `{duration}` tokens expanded
- [x] `_has_template_tokens` — detect presence of template tokens in output path
- [x] Single `--spec`: `--output` used as-is (tokens still expanded if present)
- [x] Multiple `--spec`: `--output` must contain uniqueness token; error if missing
- [x] `--spec` mutually exclusive with `--start`/`--duration`/`--end`

### Video splitting
- [x] `_calc_split_data` — compute `SplitData` from input parameters and video metadata
- [x] `_split_video` — invoke `ffmpeg` to extract segment from source video
- [x] Buffer trimming: trim to video start (0) or end when buffers overflow
- [x] `strict` policy: error if requested buffer cannot be fulfilled
- [x] `flexible` policy: trim buffer silently to video boundaries
- [x] Error when video doesn't overlap fully with desired time/duration
- [x] Input filename timestamp pattern required (unless `--raw` mode)
- [x] `--raw` mode: accept any video file, use time-only/offset rather than absolute datetime

### Multi-spec mode (`_do_main_specs`)
- [x] Process each `SpecEntry` independently
- [x] Continue on per-spec failure; report errors; exit code reflects failure count
- [x] Each spec gets its own sidecar JSON

### Sidecar JSON
- [x] `_resolve_sidecar_path` — derive sidecar path from output path and `--sidecar-json` value
- [x] `_write_sidecar` — serialise `SplitResult` to JSON file
- [x] `auto` / flag-only → `<output>.split-video.jsonl`
- [x] Explicit path → use that path (treated as template in multi-spec mode)
- [x] `none` / not specified → no sidecar created
- [x] Excluded fields not written: `success`, `input_path`, `output_path`
- [x] All `orig_*` renamed fields written correctly (see sidecar schema in spec)

### Entry point (`do_main`)
- [x] Dispatch to `_do_main_specs` when `--spec` provided
- [x] Legacy path: `--start` + (`--duration` or `--end`)

---

## Outputs

### A) Split video (`.mkv`)
- [x] Output file created by `ffmpeg` at specified path
- [x] Output directory created if missing

### B) Sidecar JSON
- [x] Fields: `buffer_before`, `buffer_after`, `orig_buffer_start`, `orig_buffer_end`,
      `buffer_duration`, `orig_buffer_offset`, `orig_start`, `orig_end`, `duration`,
      `orig_offset`, `video_width`, `video_height`, `video_frame_rate`, `video_size_mb`,
      `video_rate_mbpm`, `audio_sample_rate`, `audio_bit_depth`, `audio_channel_count`,
      `audio_codec`, `orig_device`, `orig_device_serial_number`
- [x] No absolute dates stored; times only (ISO 8601 time without date)

---

## Documentation

- [x] `split-video` added to RTD CLI index (`docs/source/cli/split-video.rst`)
- [x] `split-video` added to RTD API reference (`docs/source/api/index.rst`)

---

## Tests and Code Coverage

Test file location: `tests/qr/test_split_video.py` (mirrors `tests/qr/test_bids_inject.py` pattern).

### Timestamp / interval parsing

- [x] `_parse_ts` — full ISO 8601 datetime → correct `datetime`
- [x] `_parse_ts` — time-only string → offset from epoch / video start
- [x] `_parse_ts` — invalid string → raises `ValueError`
- [x] `_parse_interval_sec` — float seconds string → float
- [x] `_parse_interval_sec` — ISO 8601 duration string (`PT3M`) → correct seconds
- [x] `_parse_interval_sec` — invalid string → raises `ValueError`

### Spec parsing

- [x] `_parse_spec` — `START/DURATION` format → correct `SpecEntry`
- [x] `_parse_spec` — `START//END` format → correct `SpecEntry`
- [x] `_parse_spec` — time-only start with duration: `17:30:00/PT3M`
- [x] `_parse_spec` — numeric seconds start and duration: `300/180`
- [x] `_parse_spec` — invalid format (no `/`) → raises error
- [x] `_has_template_tokens` — `{n}` present → `True`
- [x] `_has_template_tokens` — no tokens → `False`
- [x] `_expand_output_template` — `{n}`, `{start}`, `{end}`, `{duration}` expanded correctly

### Core splitting logic

- [x] `_calc_split_data` — basic: start + duration within video → correct `SplitData`
- [x] `_calc_split_data` — buffer trimmed at video start (flexible policy)
- [x] `_calc_split_data` — buffer trimmed at video end (flexible policy)
- [x] `_calc_split_data` — buffer overflow with strict policy → error
- [x] `_calc_split_data` — video doesn't overlap → error

### Sidecar JSON

- [x] `_resolve_sidecar_path` — `auto` → `<output>.split-video.json`
- [x] `_resolve_sidecar_path` — explicit path → returned unchanged
- [x] `_resolve_sidecar_path` — `None` → `None`
- [x] `_write_sidecar` — all expected fields present; excluded fields absent
- [x] `_write_sidecar` — no absolute dates in sidecar (times only)

### Multi-spec mode

- [x] Single `--spec` → output used as-is
- [x] Multiple `--spec` with `{n}` token → unique output files produced
- [x] Multiple `--spec` without template token → error with descriptive message
- [x] Per-spec failure: processing continues; exit code non-zero

### Integration tests (with real or synthetic video fixture)

- [ ] Basic split: known video + known segment → output file created, duration correct
- [ ] `flexible` policy: buffer trimmed when near video boundary
- [ ] `--raw` mode: arbitrary video file split by time offset
- [ ] Sidecar JSON written with correct metadata
- [ ] Multiple `--spec` in a single invocation → all output files produced

### CLI tests (Click `CliRunner`)

- [x] `--help` renders without error
- [x] Missing `--input` → non-zero exit with error message
- [x] Missing `--output` → non-zero exit with error message
- [x] `--spec` and `--start` both provided → error (mutually exclusive)
- [x] `--duration` and `--end` both provided → error (mutually exclusive)
- [x] Neither `--spec` nor `--start` provided → error
- [x] `--lock yes` / `--lock no` → passed to `do_main` correctly
- [x] `--raw` flag → `raw=True` passed to `do_main`

### Coverage targets

| Module | Target | Current |
|---|---|---|
| `qr/split_video.py` — parsing helpers | ≥ 90% | **90%** ✓ |
| `qr/split_video.py` — overall | ≥ 80% | **90%** ✓ |
| `cli/cmd_split_video.py` | ≥ 80% | **99%** ✓ |

### Test infrastructure

- [x] Create `tests/qr/test_split_video.py`
- [x] Mock `ffmpeg` calls in unit tests (no real video fixture needed for coverage)
- [ ] Provide a small synthetic video fixture under `tests/data/split_video/` (for integration tests)
- [ ] Configure `pytest-cov` reporting for `split_video` modules

---

## Open Questions / Future Work

- [ ] **Multi-video case** — segment spanning two capture files; currently errors (issue #14)
- [ ] **`--duration` override in `bids-inject`** — `split-video` supports it; `bids-inject` could expose it
- [ ] **Conference-style batch cutting** — use `--spec` + template to replace ad-hoc scripts (e.g. distribits workflow)
- [ ] **`--raw` + `--spec`**: time-only and numeric-seconds specs work naturally; verify round-trip
- [ ] **BIDS output path template** — `--output` template tokens to embed BIDS entities directly
- [ ] **`--jobs` / parallel processing** — `--spec` list is naturally parallelisable
- [ ] **con/duct integration**
