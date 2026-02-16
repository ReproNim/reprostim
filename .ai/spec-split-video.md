# Video Split Tool Specification

## Overview

The `split-video` command is a utility to extract specific time segments from recorded video files, creating sliced output files with precise timing information and metadata.

Script (ideally in python) should take:

- location of not sliced videos
- beginning absolute time parameter
- end time or duration parameter
- optional "parameters" of how much of "buffer" to take before/after video begins/ends so we could account for time imprecision
  - all durations should accept either simple float for seconds (e.g. 121) , or ISO 8601 duration (`P2M1S`. note: isodurations does not take this value - wants a date! odd)
  - precision of `ms` is enough
  - if buffers go outside of the video times -- trim to video (so to 0 on the left, and total length on the right) and store (see below) actual values in the .json
  - if video itself doesn't overlap fully with desired time/duration -- for now just error
    - specific case: it was multiple (more than 1 video) videos captured for the single desired time duration -- we do not bother ATM to somehow join them.
- output .mkv filename.
  - in addition to .mkv generate or update (if exists) side car  .json file with annotation of the parameters etc provided into "reprostim-videocapture" field. Should contain "onset" (ISO 8601 time, no date), "duration", "buffer-before", "buffer-after" in seconds (up to .ms), all reprostim-videocapture metadata from the log (https://github.com/ReproNim/reprostim/issues/83) .
  - Do not store absolute dates anywhere. Times are ok, not dates

example:

```shell
reprostim split-video --buffer-before 10 --buffer-after 10 --start 2024-02-02T17:30:00 --duration P3M  --input $VIDEOS/2024.02.02.17.20.38.680_2024.02.02.17.20.44.774.mkv --output $BIDS/sub-01/func/sub-01_task-rest_bold.mkv
```

```shell
reprostim split-video --buffer-before 5 --buffer-after 5 --start 2025-11-05T14:03:30 --duration PT5M07S  --input temp/Videos/2025/11/2025.11.05-14.03.28.837--2025.11.05-14.13.47.757.mkv --output temp/test_split1.mkv

```

in case of input filename not satisfying the pattern to have starting time -- error


`split-video` which could be used independently of the overall setup with videos.tsv etc. Should take specification
for splitting, template for output filename(s), and overloads on command line (like buffer durations). It should have
option to produce .json file with result records depicting exact buffers etc durations (e.g. if we specified buffer
of 10 sec, but start from 2nd second, we could have only 2 seconds buffer in the beginning). Maybe add an
option `--buffer-policy=strict|flexible` so if strict, would error out if buffer cannot be fulfilled:
   - likely might be just a wrapper around `ffmpeg` invocation
   - input specification should have set of records with starttime, endtime, filename template which could potentially embed all those + extra metadata field in the record like `title`  or some other.
   - think about it to be used to produce files for a BIDS dataset (next command), so filename pattern would be to be placed into a BIDS dataset, see https://github.com/bids-standard/bids-specification/pull/2022
   - think also that this tool could potentially be used to cut up a longer video into shorter ones, like was done for full conference sessions on distribits: https://hub.datalad.org/distribits/recordings/src/branch/master/code/video_job.sh

## Enhancements

### Buffer Policy (Implemented)

Added `--buffer-policy` option with two modes:
- `strict` (default): Errors if buffers extend beyond video boundaries
- `flexible`: Automatically trims buffers to fit within video boundaries

Usage:
```shell
reprostim split-video --buffer-policy=flexible --buffer-before 10 --buffer-after 10 ...
```

### Sidecar JSON File (Implemented)

Added `-j / --sidecar-json` option to control sidecar metadata file generation:

**Behavior:**
- When NOT specified: No sidecar file is created
- When specified as `-j` or `--sidecar-json` (flag without value): Creates `<output>.split-video.jsonl`
- When specified with path as `--sidecar-json=PATH`: Uses the explicit path
- File is overwritten if it exists

**Sidecar Content:**
The sidecar JSON file contains the `SplitResult` metadata. Fields marked `exclude=True`
in the model are not serialized to the sidecar file.

**BIDS-compliant field naming:** To avoid conflicts with BIDS reserved field names
(see [BIDS PR #2022](https://github.com/bids-standard/bids-specification/pull/2022)),
the following `SplitResult` model fields are renamed with an `orig_` prefix to indicate
they describe the **original video** timing context rather than the BIDS dataset timing:

| Old field name   | New field name       |
|------------------|----------------------|
| `buffer_start`   | `orig_buffer_start`  |
| `buffer_end`     | `orig_buffer_end`    |
| `buffer_offset`  | `orig_buffer_offset` |
| `start`          | `orig_start`         |
| `end`            | `orig_end`           |
| `offset`         | `orig_offset`        |

**All sidecar fields:**

| Field                | Type    | Description                                                         |
|----------------------|---------|---------------------------------------------------------------------|
| `buffer_before`      | float   | Actual buffer before in seconds (may differ from requested if trimmed) |
| `buffer_after`       | float   | Actual buffer after in seconds (may differ from requested if trimmed)  |
| `orig_buffer_start`  | string  | Start time of the buffer segment (ISO 8601 time, no date)          |
| `orig_buffer_end`    | string  | End time of the buffer segment (ISO 8601 time, no date)            |
| `buffer_duration`    | float   | Total buffer duration in seconds                                    |
| `orig_buffer_offset` | float   | Buffer start offset in seconds from original video start            |
| `orig_start`         | string  | Start time of the split segment (ISO 8601 time, no date)           |
| `orig_end`           | string  | End time of the split segment (ISO 8601 time, no date)             |
| `duration`           | float   | Duration of the split segment in seconds                            |
| `orig_offset`        | float   | Split segment offset in seconds from original video start           |
| `video_resolution`   | string  | Video resolution (e.g., `1920x1080`)                                |
| `video_rate_fps`     | float   | Video frames per second                                             |
| `video_size_mb`      | float   | Video file size in megabytes                                        |
| `video_rate_mbpm`    | float   | Video bitrate in megabytes per minute                               |
| `audio_info`         | string  | Audio info: sample rate, channels, codec (e.g., `48000Hz 2ch aac`) |

**Example sidecar JSON:**
```json
{
  "buffer_before": 1.0,
  "buffer_after": 3.0,
  "orig_buffer_start": "00:00:00.000",
  "orig_buffer_end": "00:00:07.000",
  "buffer_duration": 7.0,
  "orig_buffer_offset": 0.0,
  "orig_start": "00:00:01.000",
  "orig_end": "00:00:04.000",
  "duration": 3.0,
  "orig_offset": 1.0,
  "video_resolution": "1920x1080",
  "video_rate_fps": 60.0,
  "video_size_mb": 8.9,
  "video_rate_mbpm": 10.2,
  "audio_info": "48000Hz 2ch aac"
}
```

**Excluded fields** (internal only, not written to sidecar):
- `success`: Whether the split operation succeeded
- `input_path`: Path to input video file
- `output_path`: Path to output video file

**Usage examples:**
```shell
# No sidecar file
reprostim split-video --start 2024-02-02T17:30:00 --duration P3M -i input.mkv -o output.mkv

# Auto-generated sidecar path: output.mkv.split-video.jsonl
reprostim split-video -j --start 2024-02-02T17:30:00 --duration P3M -i input.mkv -o output.mkv

# Explicit sidecar path
reprostim split-video --sidecar-json=/path/to/metadata.json --start 2024-02-02T17:30:00 --duration P3M -i input.mkv -o output.mkv
```

### Inline Spec Format (`--spec`)

Add a `--spec` option for compact inline segment specification. The separator token distinguishes
between duration and end-time variants:

- **`START/DURATION`** — single `/` means the right-hand part is a **duration**
- **`START//END`** — double `//` means the right-hand part is an **end time**

The option is repeatable, allowing multiple segments to be extracted in a single invocation.

**Start part** (left of `/` or `//`) accepts:
- Full ISO 8601 datetime: `2024-02-02T17:30:00`
- Time-only (with or without `T` prefix): `17:30:00`, `T17:30:00`, `17:30:00.500`
- Numeric seconds offset from video start: `300`, `300.5`

**Duration part** (right of single `/`) accepts:
- ISO 8601 duration: `PT3M`, `PT5M07S`, `P2M1S`
- Numeric seconds: `180`, `300.5`

**End part** (right of `//`) accepts:
- Full ISO 8601 datetime: `2024-02-02T17:33:00`
- Time-only: `17:33:00`, `T17:33:00`
- Numeric seconds offset from video start: `480`, `480.5`

**Parsing logic:**
1. Check if spec string contains `//` → split on first `//`, right part is end time
2. Otherwise split on first `/` → right part is duration
3. Parse left part (start) and right part (duration or end) using existing `_parse_ts` and
   `_parse_interval_sec` helpers

**Interaction with existing options:**
- `--spec` is mutually exclusive with `--start`, `--duration`, `--end`. If both are provided,
  error out.
- `--buffer-before`, `--buffer-after`, `--buffer-policy` apply globally to all specs
- `--input` is still required
- `--raw` mode applies to all specs (time-only and numeric seconds work naturally in raw mode)

#### Output naming

`--output` serves as a **template** when multiple `--spec` args are provided.

**Template tokens** (replaced in the output path):

| Token        | Description                                    | Example value  |
|--------------|------------------------------------------------|----------------|
| `{n}`        | 1-based zero-padded index (width 3)            | `001`, `002`   |
| `{start}`    | Formatted start time (dots instead of colons)  | `17.30.00.000` |
| `{end}`      | Formatted end time (dots instead of colons)    | `17.33.00.000` |
| `{duration}` | Duration in seconds                            | `180.0`        |

**Rules:**
- **Single `--spec`**: `--output` is used as-is, no template expansion needed
  (but tokens are still expanded if present).
- **Multiple `--spec`**: `--output` **must** contain at least `{n}` or another token that
  guarantees uniqueness. If no token is found, error with a descriptive message suggesting
  to add `{n}` to the output path.

#### Sidecar JSON with multiple specs

Each output file gets its **own sidecar** JSON file. The sidecar path is derived from the
resolved output path following existing rules:
- `-j` / `--sidecar-json` (flag): `<resolved_output>.split-video.json`
- `--sidecar-json=PATH`: the PATH is also treated as a template with the same tokens
  (`{n}`, `{start}`, etc.) so each spec gets a unique sidecar file.

#### Usage examples

```shell
# Single spec with duration — equivalent to --start 2024-02-02T17:30:00 --duration PT3M
reprostim split-video --spec 2024-02-02T17:30:00/PT3M \
  --buffer-before 10 --buffer-after 10 \
  -i input.mkv -o output.mkv

# Single spec with duration in seconds
reprostim split-video --spec 2024-02-02T17:30:00/180 \
  -i input.mkv -o output.mkv

# Single spec with end time (double slash)
reprostim split-video --spec 2024-02-02T17:30:00//2024-02-02T17:33:00 \
  -i input.mkv -o output.mkv

# Raw mode with time-only and duration
reprostim split-video --raw --spec 00:05:30/PT3M \
  -i any_video.mp4 -o output.mkv

# Raw mode with seconds offset and duration
reprostim split-video --raw --spec 330/180 \
  -i any_video.mp4 -o output.mkv

# Raw mode with time-only end time (double slash)
reprostim split-video --raw --spec 00:05:30//00:08:30 \
  -i any_video.mp4 -o output.mkv

# Multiple specs — extract 3 conference talks with index-based names
reprostim split-video \
  --spec 2024-02-02T09:00:00/PT25M \
  --spec 2024-02-02T09:30:00/PT20M \
  --spec 2024-02-02T10:00:00/PT30M \
  --buffer-before 5 --buffer-after 5 \
  -i conference_recording.mkv \
  -o talks/talk_{n}.mkv
# produces: talks/talk_001.mkv, talks/talk_002.mkv, talks/talk_003.mkv
#           talks/talk_001.mkv.split-video.json, etc. (when -j is used)

# Multiple specs with time-based output names
reprostim split-video \
  --spec 14:00:00/PT5M \
  --spec 14:10:00//14:15:00 \
  -j -i input.mkv \
  -o segments/seg_{n}_{start}.mkv
# produces: segments/seg_001_14.00.00.000.mkv, segments/seg_002_14.10.00.000.mkv
#           segments/seg_001_14.00.00.000.mkv.split-video.json, etc.

# Multiple specs — error case (no uniqueness token)
reprostim split-video \
  --spec 14:00:00/PT5M \
  --spec 14:10:00/PT3M \
  -i input.mkv -o output.mkv
# ERROR: multiple --spec provided but --output contains no template token.
#        Add {n} to output path, e.g.: -o output_{n}.mkv
```

#### Error handling

- If `--spec` format is invalid (missing `/`, unparseable parts), error with descriptive message
- If `--spec` and `--start`/`--duration`/`--end` are both provided, error immediately
- If multiple `--spec` and `--output` has no template token, error with suggestion
- Each spec is validated independently against video boundaries (same rules as current behavior)
- If any spec fails in a multi-spec run, report the error but continue processing remaining specs
  (exit code reflects the number of failures, or a non-zero code if any failed)

?? **Open question**: on failure in multi-spec mode, should it stop at first error or continue
processing remaining specs? "Continue and report" seems more useful for batch workflows.
