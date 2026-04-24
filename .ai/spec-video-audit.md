# Video Audit Tool Specification

## Overview

`video-audit` analyzes video files recorded by `reprostim-videocapture`, along with their
corresponding `.log` sidecar files and QR/audio metadata. It extracts key information about
each recording and produces a summary table (`videos.tsv`) suitable for quality control,
sharing, and further analysis.

The tool operates in a pipeline of up to three audit sources:

1. **INTERNAL** — fast pass using `mediainfo`/ffprobe and `.log` sidecars; always runs first
2. **NOSIGNAL** — slow pass using `reprostim detect-noscreen` to measure no-signal frame rate
3. **QR** — very slow pass using `reprostim qr-parse` to count detected QR records per video

Results are accumulated into a TSV file (`videos.tsv`) with timestamp-aware merging so that
incremental updates from different sources are combined correctly.

---

## CLI Interface

```
reprostim video-audit [OPTIONS] [PATHS]...
```

### Arguments

| Argument  | Description                                                                     |
|-----------|---------------------------------------------------------------------------------|
| `PATHS`   | One or more paths to video files (`.mkv`, `.mp4`, `.avi`) or directories. Required. |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-m / --mode` | Choice | `incremental` | Operation mode (see [Modes](#modes)) |
| `-o / --output` | Path | `videos.tsv` | Output TSV file |
| `-r / --recursive` | Flag | `False` | Recursively scan subdirectories |
| `-s / --audit-src` | Choice (repeatable) | `internal` | Audit source(s) to run (see [Sources](#audit-sources)) |
| `-l / --max-files` | Int | `-1` | Max number of files/records to process; `-1` = unlimited |
| `-p / --path-mask` | Str | `None` | fnmatch-style filter on file paths |
| `-v / --verbose` | Flag | `False` | Print each record as JSON to stdout |
| `-n / --nosignal-opts` | Str | `None` | Override default options passed to `detect-noscreen` (shlex-parsed string); uses built-in defaults when omitted |
| `-q / --qr-opts` | Str | `None` | Extra options passed to `qr-parse` (shlex-parsed string); no extra options by default |
| `-c / --config` | Path | `None` | Optional YAML config file; provides defaults for any option not set on the CLI (see [Config File](#config-file)) |

### Example invocations

```shell
# Incremental audit of a directory (INTERNAL only, fast)
reprostim video-audit /data/recordings/

# Full re-audit including QR and nosignal sources
reprostim video-audit --mode full -s all /data/recordings/ -o videos.tsv

# Recursive scan, incremental, QR only
reprostim video-audit -r -s qr /data/recordings/

# Rerun only nosignal for records that currently show n/a
reprostim video-audit --mode rerun-for-na -s nosignal /data/recordings/

# Reset QR results to n/a (to force a clean rerun later)
reprostim video-audit --mode reset-to-na -s qr /data/recordings/

# Limit to first 5 files, verbose JSON output
reprostim video-audit -l 5 -v /data/recordings/

# Override detect-noscreen parameters
reprostim video-audit -s nosignal \
  --nosignal-opts "--number-of-checks 200 --threshold 0.9" \
  /data/recordings/

# Pass extra options to qr-parse
reprostim video-audit -s qr \
  -q "--skip 2 --std-threshold 15" \
  /data/recordings/

# Use a YAML config file for defaults, override one option on the CLI
reprostim video-audit -c audit.yaml -s nosignal /data/recordings/
```

---

## Config File

`-c / --config` accepts an optional path to a YAML file. Values in the config file act as
defaults — any option explicitly passed on the CLI takes precedence.

Keys mirror the CLI long option names (hyphens, no leading `--`). Supported keys:

```yaml
# audit.yaml — example config
mode: incremental
output: videos.tsv
recursive: false
audit-src:
  - internal
  - qr
max-files: -1
path-mask: null
verbose: false
nosignal-opts: "--number-of-checks 200 --threshold 0.9"
qr-opts: "--skip 2 --std-threshold 15"
```

Precedence (lowest → highest): built-in CLI defaults → config file → explicit CLI flags.

---

## Modes

| Mode | Description |
|------|-------------|
| `incremental` | Process only new files not present in the existing TSV; merge results |
| `full` | Regenerate all records from scratch, overwrite existing TSV completely |
| `force` | Redo/overwrite existing records for the specified files |
| `rerun-for-na` | Re-run external tools only for records whose related fields are `n/a` |
| `reset-to-na` | Reset external-tool fields (`no_signal_frames`, `qr_records_number`) to `n/a` |

---

## Audit Sources

| Source | Speed | Description |
|--------|-------|-------------|
| `internal` | Fast | Uses ffprobe + `.log` sidecar; extracts timestamps, resolution, FPS, audio, duration |
| `nosignal` | Slow | Runs `reprostim detect-noscreen`; stores `nosignal_rate` as a percentage |
| `qr` | Very slow | Runs `reprostim qr-parse` via ffmpeg-stripped temp copy; stores `qr_count` |
| `all` | — | Runs all three sources above |

Sources can be combined: `-s internal -s qr` runs both INTERNAL and QR passes.

---

## Output: `videos.tsv`

Tab-separated file. One row per video file, columns defined by `VaRecord`:

| Column | Description |
|--------|-------------|
| `path` | Absolute path to the `.mkv` file |
| `present` | Whether the file exists on disk |
| `complete` | Whether end timestamp is present in log |
| `name` | Short base name (used as merge key) |
| `start_date` / `start_time` | Recording start (`YYYY-MM-DD`, `HH:MM:SS.mmm`) |
| `end_date` / `end_time` | Recording end (`YYYY-MM-DD`, `HH:MM:SS.mmm`) |
| `video_res_detected` | Resolution from `session_begin` log entry, e.g. `1920x1080` |
| `video_fps_detected` | FPS from `session_begin` log entry |
| `video_dur_detected` | Duration from mediainfo (seconds) |
| `video_res_recorded` | Resolution from `qr_parse.do_parse` |
| `video_fps_recorded` | FPS from `qr_parse.do_parse` |
| `video_dur_recorded` | Duration from `qr_parse.do_parse` (seconds) |
| `video_size_mb` | File size in MB |
| `video_rate_mbpm` | Bitrate in MB/min |
| `audio_sr` | Audio sample rate + bit depth + channels + codec |
| `audio_dur` | Audio stream duration (seconds) |
| `duration` | Best-available duration (seconds) |
| `duration_h` | Human-readable duration (`HH:MM:SS.mmm`) |
| `no_signal_frames` | No-signal percentage from `detect-noscreen`, or `n/a` |
| `qr_records_number` | QR record count from `qr-parse`, or `n/a` |
| `file_log_coherent` | Whether video/audio metadata is internally consistent |
| `no_signal_updated_on` | Timestamp of last nosignal update |
| `qr_updated_on` | Timestamp of last QR update |
| `updated_on` | Timestamp of last INTERNAL update |

Sentinel values for `qr_records_number`:
- `n/a` — not yet processed
- `-2` — ffmpeg conversion started but qr-parse not yet invoked
- `-1` — qr-parse completed but no `ParseSummary` record found in output
- `≥ 0` — actual QR record count

---

## Derived Output Files

### NOSIGNAL data
- JSON output: `derivatives/nosignal/<YYYY>/<MM>/<basename>.nosignal.json`
- Log output: `logs/nosignal/<YYYY>/<MM>/<basename>.nosignal.log`
- Directories configurable via `VaContext.nosignal_data_dir` / `nosignal_log_dir`

### QR data
- JSONL output: `derivatives/qr/<YYYY>/<MM>/<basename>.qrinfo.jsonl`
- Log output: `logs/qr/<YYYY>/<MM>/<basename>.qrinfo.log`
- ffmpeg log: `logs/qr/<YYYY>/<MM>/<basename>.ffmpeg.log`
- Directories configurable via `VaContext.qr_data_dir` / `qr_log_dir`

---

## Concurrency and Locking

- `videos.tsv` is protected by a `filelock.FileLock` (`videos.tsv.lock`) during all reads and writes.
- Each video file gets per-source lock files (`.nosignal.lock`, `.qr.lock`) to prevent concurrent
  processing of the same file by multiple processes.
- `_get_tsv_records` supports a `use_lock=False` dirty-read mode for callers that cannot acquire
  the lock (e.g. different OS user) — used by `bids-inject`.

---

## Merge Strategy

The TSV is updated using a three-way timestamp-aware merge:

- `updated_on` — controls which process wrote the INTERNAL fields
- `no_signal_updated_on` — controls which process wrote `no_signal_frames`
- `qr_updated_on` — controls which process wrote `qr_records_number`

When a record exists in both the current TSV and the new batch, `_merge_rec` picks the
**newest** value for each group of fields independently, allowing INTERNAL, NOSIGNAL, and QR
results from separate runs to coexist correctly.

---

## Python API

Key public symbols in `reprostim.qr.video_audit`:

| Symbol | Type | Description |
|--------|------|-------------|
| `VaRecord` | Pydantic model | Single TSV row |
| `VaContext` | Pydantic model | All processing options including `nosignal_opts`, `qr_opts` |
| `VaMode` | Enum | Operation modes |
| `VaSource` | Enum | Audit sources |
| `do_audit_file` | Generator | Audit a single video file (INTERNAL) |
| `do_audit_dir` | Generator | Audit all videos in a directory |
| `do_audit` | Generator | Full pipeline (INTERNAL + external) |
| `do_ext` | Generator | External-only pass over existing records |
| `do_main` | Function | CLI entry point; accepts `nosignal_opts` and `qr_opts` as shlex strings |
| `get_file_video_audit` | Function | Look up a single file (TSV cache or live audit) |
| `find_video_audit_by_timerange` | Function | Intersect-based lookup used by `bids-inject` |

---

## Dependencies

- **ffprobe** (`ffmpeg` package) — required for audio stream extraction
- **mediainfo** — used internally via `qr_parse.do_info_file`
- **reprostim detect-noscreen** — required for NOSIGNAL source
- **reprostim qr-parse** — required for QR source
- **ffmpeg** — required for QR source (audio stripping before qr-parse)
- **filelock** — advisory locking for TSV and per-file operations

---

## Open Questions / Future Work

- **Parallel processing** — `--jobs` option for concurrent file processing
- **Progress reporting** — tqdm progress bar for large directories
- **DataLad integration** — auto-`datalad save` after TSV update
- **`--columns` filter** — select which TSV columns to populate per run
