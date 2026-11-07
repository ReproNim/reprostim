# BIDS QR Inject Tool Specification

## Overview

`bids-qr-inject` is a CLI command that takes the ReproStim media files already injected into a
BIDS dataset by [`bids-inject`](inject-spec.md) (the dedicated `_recording-reprostim_*.mkv` rows
of `_scans.tsv`, issue #276), reads the QR codes embedded in that media (decoded by
[`qr-parse`](../qr/parse-spec.md), `*.qrinfo.jsonl` records) and injects the result into the BIDS
dataset as:

- extra `_scans.tsv` columns on the media row (QR summary + timing/duration facts),
- a BIDS `_events.tsv`-like file with one row per decoded QR code (`trial_type = qr`),
- the matching `_events.json` data dictionary (new levels, optionally HED tags),
- `scans.json` documentation for the new `_scans.tsv` columns.

Corresponds to GitHub issue: https://github.com/ReproNim/reprostim/issues/275
Related: #276 (dedicated media row in `_scans.tsv`), #14 (`bids-qr-sync`, date offset),
#281 (media row `duration`), #259 ([`bids-inject-sidecar`](inject-sidecar-spec.md)),
[bids-utils #10](https://github.com/bids-standard/bids-utils/issues/10) (consistent date
anonymization), BEP044 media files (bids-standard/bids-specification PR #2367).

**Status: specification only — nothing is implemented yet.** See
[qr-inject-tasks.md](qr-inject-tasks.md) for the checklist. Everything below that is not stated in
the issue is a **proposal** and is listed in [Open Questions / TODOs](#open-questions--todos).

> **Naming.** The issue title reads "bids-qr-inject to add mode to inject QR codes into BIDS",
> and the issue also lists `--anonymize-dates`/`--date-offset` options. This spec treats
> `bids-qr-inject` as a **new, separate command** (the follow-on tool already referenced from
> [inject-spec.md](inject-spec.md) Output D and its Future Work), not as a new `--qr` mode of
> `bids-inject` (whose `--qr [none|auto|embed-existing|parse]` option is reserved for timing
> refinement, not for output generation). See Open Question #1.

---

## Motivation

`bids-inject` slices the stimuli video for each scan and writes the media file, its sidecar and
the `_scans.tsv` media row. The video itself contains the most precise record of what the
participant saw (QR codes shown by `timesync-stimuli`: scanner triggers, series, acquisition
counters, wall-clock times). Today this information stays in the `derivatives/qr/**/*.qrinfo.jsonl`
files and is not discoverable from the BIDS dataset. Injecting it gives:

- **Exact stimulus timing in BIDS form** (`_events.tsv`), usable by BIDS-aware analysis tools.
- **A sync check**: `qr_first_trigger_offset` (seconds from the clip start to the first scanner
  trigger QR code) should equal `reprostim_buffer_before` when NTP-based clocks and the injected
  buffer are exact. A non-zero difference measures the real clock/scan misalignment; if the
  synchronization is trustworthy the buffer could be dropped (issue #275).
- **Per-clip facts** (`video_duration`, `video_framecount`, absolute times) next to the scan row.

---

## Inputs

| Input                        | Description                                                                                                                                      |
|------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| BIDS `_scans.tsv` files      | Same `PATHS` convention as `bids-inject` (files or directories, `--recursive`). Only **media rows** (`ScanRecordKind.is_reprostim_media`) are processed; acquisition rows and `UNKNOWN` rows are left untouched. |
| Injected media file          | `*_recording-reprostim_{video,audio,audiovideo}.mkv` referenced by the media row `filename`. Must exist (error otherwise), may be a symlink / git-annex pointer. |
| QR records (`.qrinfo.jsonl`) | One JSON `QrRecord` per line (`qr/parse.py::QrRecord`: `index`, `frame_start/end`, `isotime_start/end`, `time_start/end`, `duration`, `data`) plus the leading `ParseSummary`. Source selected by [`--qr`](#qr-sources---qr). |
| `videos.tsv` (optional)      | `-f / --videos`, used to resolve the source video of a media row (`reprostim_path`) and its cached QR location when `--qr` needs it.              |

---

## Outputs

All outputs are produced **per media row**, next to the media file. Examples use the layout from
`bids-inject` Output A:

```
sub-qa/ses-20250814/func/sub-qa_ses-20250814_acq-faX77_recording-reprostim_audiovideo.mkv   # input
sub-qa/ses-20250814/func/sub-qa_ses-20250814_acq-faX77_recording-reprostim_events.tsv       # output B
sub-qa/ses-20250814/func/sub-qa_ses-20250814_acq-faX77_recording-reprostim_events.json      # output C
```

### A) `_scans.tsv` — extra columns on the media row

New columns appended to the **same dedicated media row** that `bids-inject` created (never to the
acquisition row), continuing the pattern of issue #276. Names are the ones proposed in issue #275:

| Column                         | Source                                                                            | Description                                                                                                  |
|--------------------------------|-----------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `qr_count`                     | number of unique `QrRecord`s                                                      | Count of unique decoded QR codes in the clip (consecutive frames of the same QR are already collapsed by `qr-parse`). |
| `qr_first_trigger_offset`      | first trigger QR `time_start`                                                     | Seconds from the clip start to the first "trigger" QR code. Should match `reprostim_buffer_before` when sync is exact. `n/a` if none. |
| `qr_first_trigger_abstime`     | first trigger QR `data` wall-clock time                                           | Clock time parsed from the QR code payload (subject to [date anonymization](#date-anonymization)). `n/a` if none. |
| `reprostim_isotime_full`       | start time of the **source** video                                                | Absolute start of the full source recording (from the video file name / `VideoTimeInfo`).                    |
| `reprostim_isotime_offset`     | `isotime` of the clip start                                                        | Absolute time of the first frame of the injected clip (= source start + `reprostim_offset`).                 |
| `video_duration`               | media file                                                                         | Clip duration in seconds (`ffprobe`/`video_audit`; same value family as `duration` of the media row).        |
| `video_framecount`             | media file                                                                         | Number of video frames in the clip.                                                                          |

> **"Trigger" QR code** = a QR record whose `data.event == "trigger"`
> (`qr/psychopy.py::EventType.MRI_TRIGGER_RECEIVED`).

Unavailable values are written as BIDS `n/a`. Existing columns of the row (`filename`, `acq_time`,
`duration`, `reprostim_*` from `bids-inject`) are never modified. Re-running the tool updates the
new columns in place (idempotent, no duplicate rows), following the insert-or-update rules of
[inject-spec.md](inject-spec.md#insert-or-update-idempotency-and-sort-order).

### B) `_events.tsv` — one row per decoded QR code

Built from the `QrRecord`s of the clip; BIDS-style tab-separated file with `n/a` for missing values.
The `_events` suffix is the placeholder already used by
[inject-spec.md](inject-spec.md#c-qr-codes-file--bids-events-like-tsv); the final suffix
(`_qrcodes`, `_codes`, `_qr`, `_qrinfo`, …) is still undecided — see Open Question #3.

| Column         | Source `QrRecord` field    | Description                                                                                   |
|----------------|----------------------------|-----------------------------------------------------------------------------------------------|
| `onset`        | `time_start` (or frame/rate) | Seconds from the **first frame of the media file** to the QR code appearance. Derived from the audio/video sampling rate (frame number / frame rate), not from wall-clock. |
| `duration`     | `duration` / `time_end - time_start` | Seconds the QR code stayed visible.                                                  |
| `trial_type`   | constant                   | `qr` for every row (leaves the value space open for future event kinds, e.g. BIRCH events).   |
| `isotime_start`| `isotime_start`            | Absolute start time (subject to [date anonymization](#date-anonymization)).                   |
| `isotime_end`  | `isotime_end`              | Absolute end time (same).                                                                     |
| `frame_start`  | `frame_start`              | First frame the QR code was seen in.                                                           |
| `frame_end`    | `frame_end`                | Last frame the QR code was seen in.                                                            |
| `data`         | `data`                     | The full decoded QR payload as a compact JSON string (single line, tabs/newlines escaped).    |

Rows are sorted by `onset`. Only these columns are written initially; the issue also considered
mapping individual payload keys (acquisition/series numbers, keys, wall-clock times, audio data)
to dedicated columns but suggests **skipping** them — the full record stays available in `data`.

### C) `_events.json` — data dictionary

A BIDS data dictionary describing every column of output B and the `trial_type` level `qr`
(`LongName`/`Description`/`Units`/`Levels`, same shape as
`src/reprostim/assets/bids/scans.json`). Proposed to ship as a package asset
(`src/reprostim/assets/bids/events.json`) and copied next to each events file (or placed once at
the dataset/subject level by the BIDS inheritance principle — Open Question #5).

Per the issue, `trial_type` level `qr` should carry **HED tags** describing the visual stimulus
(a QR-code image displayed on screen). Suggested process: take a sample QR image, use an online
image-annotation tool to generate candidate HED tags, review them manually, and validate the
result with the HED tools. Examples of the expected shape exist in `bids-examples`.

### D) `scans.json`

`src/reprostim/assets/bids/scans.json` (the `_scans.tsv` data dictionary written by `bids-inject`)
gets entries for all seven new columns of output A (`LongName`, `Description`, `Units` where
applicable: `s` for offsets/durations, `frames` is unit-less).

---

## CLI Interface

```
reprostim bids-qr-inject [OPTIONS] PATHS...
```

`PATHS` and path resolution follow [`bids-inject`](inject-spec.md#path-resolution-rules)
(one or more `_scans.tsv` files or directories; directories are searched non-recursively unless
`-r`).

### Options

Options shared with `bids-inject` keep the **same short/long names and semantics**.

| Option                                          | Type            | Default | Description                                                                                                                   |
|-------------------------------------------------|-----------------|---------|-------------------------------------------------------------------------------------------------------------------------------|
| `-d / --dataset PATH`                           | Path (dir)      | `.`     | Home directory of the BIDS dataset.                                                                                           |
| `-r / --recursive`                              | Flag            | False   | Recurse into subdirectories to find all `*_scans.tsv` files.                                                                  |
| `-f / --videos PATH`                            | Path            | none    | Optional `videos.tsv` to locate the source video / cached QR data of each media row.                                          |
| `-q / --qr [auto\|embed-existing\|parse]`       | Choice          | `auto`  | Where QR records come from, see [QR sources](#qr-sources---qr). (`none` does not exist here — the tool is useless without QR.) |
| `-m / --match REGEX`                            | String          | `.*`    | Only process media rows whose `filename` matches.                                                                              |
| `-i / --ignore-path PATH_OR_GLOB`               | String (repeatable) | none | File, directory or `fnmatch` glob to skip, relative to `--dataset`.                                                          |
| `--anonymize-dates [strip\|none\|offset]`       | Choice          | `strip` | Date handling for absolute times written by this tool, see [Date anonymization](#date-anonymization).                          |
| `--date-offset DAYS`                            | int             | none    | Days subtracted from every date with `--anonymize-dates offset`; same option as proposed in issue #14.                          |
| `-w / --overwrite [skip\|force\|always\|error]` | Choice          | `skip`  | Policy for existing `_events.tsv`/`_events.json` (same semantics as `bids-inject`; `_scans.tsv` columns are always refreshed). |
| `-n / --dry-run`                                | Flag            | False   | Resolve and report what would be written; write nothing.                                                                       |
| `-v / --verbose`                                | Flag            | False   | Increase verbosity.                                                                                                            |

Config file support (`-c / --config`, [config-spec.md](../cli/config-spec.md)): the command gets a
`bids_qr_inject` section; the LinkML schema needs a `BidsQrInjectConfig` class (and a root slot)
with the same snake_case names (`anonymize_dates`, `date_offset`, `ignore_paths`, …); the
generated Pydantic model and RTD JSON schema are regenerated with `make generate-config`.

### Example invocations

```shell
# One session of a dataset, QR records taken from the media file itself if no cache is found
reprostim bids-qr-inject --dataset /data/ds sub-qa/ses-20250814/sub-qa_ses-20250814_scans.tsv

# Whole dataset, use only already parsed qrinfo.jsonl, keep real dates (QA data)
reprostim bids-qr-inject -d /data/ds -r --qr embed-existing --anonymize-dates none .

# Real data: strip dates, keep times of day (default)
reprostim bids-qr-inject -d /data/ds -r --anonymize-dates strip .

# Shift all dates by a fixed number of days (to a date before 1925)
reprostim bids-qr-inject -d /data/ds -r --anonymize-dates offset --date-offset 36500 .

# Dry-run on functional scans only
reprostim bids-qr-inject -d /data/ds -r --match '^func/' --dry-run .
```

---

## QR sources (`--qr`)

| Mode             | Behaviour                                                                                                                                                  |
|------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `embed-existing` | Use already parsed QR JSONL. Error for a media row if none is found.                                                                                        |
| `parse`          | Always run `qr-parse` on the injected media file (works on a clip alone, no source video / `derivatives/` needed).                                          |
| `auto` (default) | Use existing JSONL when available, otherwise fall back to `parse`.                                                                                          |

Two kinds of existing JSONL are possible and the choice is an open design point (Open Question #2):

1. **Per source video** (`derivatives/qr/<YYYY>/<MM>/<basename>.qrinfo.jsonl`, produced by
   `video-audit`): records are relative to the *source* recording, so they must be clipped to the
   injected window and re-based using `reprostim_offset` and the clip duration (frame numbers and
   `time_*` shifted, records outside the window dropped).
2. **Per injected clip**: records are already relative to the clip; no re-basing.

Frame accuracy is better when decoding the clip itself (`parse`); the cached path is much faster.

---

## Date anonymization

All **absolute times** this tool writes (`qr_first_trigger_abstime`, `reprostim_isotime_*`,
`isotime_start/end`, and any timestamps inside `data`) are subject to `--anonymize-dates`
(issue #275; consistent with bids-utils #10 and the `--date-offset` of issue #14):

| Value    | Behaviour                                                                                                                         |
|----------|-----------------------------------------------------------------------------------------------------------------------------------|
| `strip`  | **Default, safe for real data.** Remove the date, keep the time of day (proposed placeholder date `1900-01-01`, the BIDS convention for anonymized `acq_time`). |
| `none`   | Keep dates unchanged. Suited to QA/phantom data.                                                                                   |
| `offset` | Subtract `--date-offset` days from each date (typically to a date before 1925); times of day unchanged. `--date-offset` is required for this mode. |

Relative values (`onset`, `duration`, `qr_first_trigger_offset`, `video_*`) are never affected.
Anonymization must be applied consistently inside the free-form `data` JSON as well, otherwise
real dates leak through that column (Open Question #4).

---

## Algorithm / Data Flow

```
1. Resolve PATHS → list of _scans.tsv files (same walker as bids-inject; --recursive, --ignore-path).
2. Validate options: --anonymize-dates offset requires --date-offset; dataset exists.
3. For each _scans.tsv:
   a. Parse it with the bids-inject scans model; select media rows
      (kind.is_reprostim_media) whose filename matches --match.
   b. For each media row:
      i.   Resolve the media file path; missing → error for this row, continue.
      ii.  Obtain QR records per --qr (embed-existing | parse | auto), re-basing source-video
           JSONL to the clip window when needed.
      iii. Compute the A) summary: qr_count, first trigger (offset/abstime), isotime_full/offset,
           video_duration, video_framecount (ffprobe / media_info).
      iv.  Apply date anonymization to every absolute time.
      v.   Build B) events rows; write _events.tsv according to --overwrite (skip unless --dry-run).
      vi.  Write the C) _events.json data dictionary next to it.
      vii. Update the media row's new columns in memory.
   c. Write the updated _scans.tsv atomically (and D) scans.json) unless --dry-run.
4. Print summary "N rows processed, M written, K errors"; exit code non-zero on any error.
```

---

## Error Handling

- Missing media file, unreadable/invalid JSONL, `qr-parse` failure → error for **that row**, other
  rows continue; overall exit code non-zero.
- No QR codes found in a clip is **not** an error: `qr_count = 0`, other QR columns `n/a`, an
  empty (header-only) `_events.tsv` is written.
- `--anonymize-dates offset` without `--date-offset` → fatal before any file is touched.
- `--qr embed-existing` and no JSONL found for a row → error for that row.
- Malformed existing `_scans.tsv` → error for that file, no partial write.

---

## Implementation Plan (proposed layout)

| Item                                         | Notes                                                                                           |
|----------------------------------------------|-------------------------------------------------------------------------------------------------|
| `src/reprostim/bids/qr_inject.py`            | `do_main(...)`, `QiContext` (mirrors `BiContext`/`BisContext`), `_do_qr_inject_*` helpers.        |
| `src/reprostim/cli/cmd_bids_qr_inject.py`    | Click command `bids-qr-inject`; propagate the result with `ctx.exit(res)` ([exit-codes-spec.md](../cli/exit-codes-spec.md)). Registered in `entrypoint.py`. |
| Reuse                                        | `bids/inject.py` scans model & walker (`ScanRecord`, `ScanRecordKind`), `qr/parse.py` (`QrRecord`, `qr-parse` API), `video/media_info.py` + `bids/properties.py` (duration/framecount), `bids/media.py`. If helpers are private to `inject.py`, extract the shared ones instead of duplicating. |
| `src/reprostim/assets/bids/events.json`      | Data dictionary asset (C); `scans.json` extended (D).                                           |
| Config schema                                | `bids_qr_inject` class/slot in `config.linkml.yaml`, regenerate model and JSON schema.            |
| Docs                                         | `docs/source/cli/bids-qr-inject.rst` (+ `cli/index.rst`), changelog; `.ai/context.md` entries.   |
| Tests                                        | `tests/bids/test_qr_inject.py`, `tests/cli` options layer via `CliRunner`.                        |

---

## Open Questions / TODOs

1. **Command vs mode.** The issue title speaks of "adding a mode"; this spec assumes a new
   `bids-qr-inject` command (as `inject-spec.md` already assumes). Confirm, including whether
   `--anonymize-dates`/`--date-offset` should *also* be added to `bids-inject` (they are listed
   in the issue and would then apply to `acq_time` of `_scans.tsv`).
2. **QR source for `auto`/`embed-existing`**: per-source-video JSONL with re-basing vs per-clip
   JSONL; where cached JSONL is looked up (`--videos` + `derivatives/qr/`, a `--qr-dir` option, or next to the media).
3. **Final suffix** of the QR events file (`_events` vs `_qrcodes`/`_codes`/`_qr`/`_qrinfo`);
   `_events` is reserved for BIRCH device events per `inject-spec.md`. Affects output B/C names and the
   `trial_type` rationale.
4. **Date anonymization details**: placeholder date for `strip`; how to sanitize dates inside `data`
   (known keys vs recursive ISO-string rewrite); whether `reprostim_isotime_*` and the existing
   `acq_time`/`reprostim_*` columns of `bids-inject` need the same treatment.
5. **`events.json` placement**: per recording vs once at dataset level (BIDS inheritance).
6. **Column naming**: issue names are used as-is; decide whether `qr_*`/`video_*` should get the
   `reprostim_` prefix like the `bids-inject` columns (`reprostim_buffer_before`, …).
7. **Exact semantics of `onset`** for clips with a leading buffer (relative to the clip start, as
   specified, vs relative to the scan onset = clip start + `reprostim_buffer_before`).
8. **Skipping the buffer.** If `qr_first_trigger_offset` proves equal to `reprostim_buffer_before`
   in practice, document guidance on dropping the buffer (issue #275).
9. **HED tags** for the QR stimulus: generate with an annotation tool, review manually, validate
   with the HED validator.
10. `--lock [yes|no]` for `videos.tsv` (dirty-read) if `--videos` is used, same as `bids-inject`.
11. Resume/validation with the future `bids-qr-sync` tool (issue #14) — keep the written columns
    consistent with what that tool will need.
