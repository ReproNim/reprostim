# BIDS Inject Tool Specification

## Overview

The `bids-inject` command is a higher-level orchestration tool that integrates ReproStim video
recordings into a BIDS (Brain Imaging Data Structure) dataset. It cross-references the ReproStim
`videos.tsv` inventory with BIDS `_scans.tsv` files to identify which video segments correspond
to which functional (or other) MRI acquisitions, then delegates to `split-video` to extract and
place the correctly-timed video clips into the BIDS dataset.

Corresponds to GitHub issue: https://github.com/ReproNim/reprostim/issues/14

---

## Motivation

During an fMRI session, `reprostim-videocapture` continuously records long `.mkv` files that
may span multiple scan runs. After the session, researchers need individual video clips that
precisely match each DICOM series so that:

- The stimulus video for `sub-01/func/sub-01_task-rest_bold.nii.gz` can be found as
  `sub-01/func/sub-01_task-rest_bold.mkv` (plus a sidecar `.json`).
- Timing metadata (onset, duration, actual buffers) is stored alongside the BIDS data.
- No manual per-run slicing is required.

---

## Inputs

| Source              | Description                                                                                                                                                                                          |
|---------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `videos.tsv`        | ReproStim video inventory (produced by `video-audit`). Contains per-file paths, start/end timestamps, duration, completeness flags. Video file paths are resolved relative to `videos.tsv` location. |
| BIDS `_scans.tsv`   | Per-subject/session scan manifest. Contains `filename` (relative BIDS path) and `acq_time` (ISO 8601 datetime of scan start).                                                                        |
| DICOM JSON sidecars | `*_bold.json` / `*_T1w.json` etc. Contain `AcquisitionTime` array and/or `FrameAcquisitionDuration` for computing scan duration.                                                                     |
| CLI options         | Buffer sizes, buffer policy, time-offset, QR mode, _scan.tsv path.                                                                                                                                   |

---

## Outputs

For each matched BIDS acquisition, up to three files are produced:

### A) Media file — BEP044:Stimuli

A sliced `.mkv` recording of the stimulus presented during the scan. The filename uses the same
basename as the source NIfTI but replaces the BIDS suffix with a recording-type suffix per
[BEP044:Stimuli](https://bids.neuroimaging.io/bep044):

- `_recording-reprostim_video.mkv` — video only
- `_recording-reprostim_audio.mkv` — audio only
- `_recording-reprostim_audiovideo.mkv` — combined audio+video (typical for ReproStim `.mkv`)

The media type suffix is determined from the source video's `videos.tsv` metadata produced by
`video-audit`. The relevant columns are `audio_sr` (audio sample rate / stream info) and
`video_res_detected` (detected video resolution):

| `video_res_detected` | `audio_sr`     | Suffix        |
|----------------------|----------------|---------------|
| present              | absent / `n/a` | `_video`      |
| absent / `n/a`       | present        | `_audio`      |
| present              | present        | `_audiovideo` |
| absent / `n/a`       | absent / `n/a` | skip/warn     |

If neither stream is detected the file is skipped with a warning.

Example (nearby layout):
```
sub-qa/ses-20250814/func/sub-qa_ses-20250814_acq-faX77_recording-reprostim_audiovideo.mkv
```

### B) Sidecar metadata — BEP047:Behavior + ReproStim extras

A `.json` file with the same basename as the media file (A), following
[BEP047:Behavior](https://bids.neuroimaging.io/bep047) conventions and extended with
ReproStim-specific fields from the capture logs. Contains onset, duration, actual buffer
values, source video path, and other reprostim-videocapture metadata.
**No absolute dates stored; times only.**

Example:
```
sub-qa/ses-20250814/func/sub-qa_ses-20250814_acq-faX77_recording-reprostim_audiovideo.json
```

### C) QR codes file — BIDS _events-like .tsv

If QR codes were parsed from the video (`--qr` mode is not `none`), the decoded QR records
are written in BIDS-compliant tabular form (columns: `onset`, `duration`, plus QR-derived
fields) and is only produced when QR data is available and successfully parsed.

```
sub-qa/ses-20250814/func/sub-qa_ses-20250814_acq-faX77_recording-reprostim_events.tsv
```

> **Note — suffix naming is under revision.** The `_events` suffix used above is a placeholder.
> The final suffix name has not been decided yet; candidates include:
> `_qrcodes`, `_codes`, `_qr`, `_qrinfo`.
>
> The `_events` suffix should be reserved for a separate, future output containing metadata
> from the **BIRCH device** and its connected subdevice events (triggers, button presses, etc.),
> which is a distinct concept from the QR code log. The QR codes file suffix will be renamed
> once the BIDS naming convention is settled.

---

## CLI Interface

```
reprostim bids-inject [OPTIONS] PATHS...
```

### Arguments

| Argument  | Description                                                                                                                                                                                                                                                             |
|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `PATHS`   | One or more paths to process. Each path can be: a `_scans.tsv` file (processed directly); a session directory (searched for `*_scans.tsv` files); or a dataset/subject root directory (searched recursively when `--recursive` is set). At least one path is required.  |

### Path resolution rules

- **`*_scans.tsv` file** — processed directly.
- **Directory** — searched for `*_scans.tsv` files in its immediate children (non-recursive by
  default). With `--recursive`, all `*_scans.tsv` files found anywhere under the directory are
  collected and processed.
- Multiple paths of any mix of the above are accepted in a single invocation.

### Options

| Option                                          | Type            | Default    | Description                                                                                                                 |
|-------------------------------------------------|-----------------|------------|-----------------------------------------------------------------------------------------------------------------------------|
| `-f / --videos PATH`                            | Path            | required   | Path to `videos.tsv` produced by `video-audit`. Video file paths in the TSV are resolved relative to this file's location. |
| `-r / --recursive`                              | Flag            | False      | When a directory is given in PATHS, recurse into subdirectories to find all `*_scans.tsv` files.                            |
| `-b / --buffer-before DURATION`                 | sec or ISO 8601 | `0`        | Extra video before scan onset.                                                                                              |
| `-a / --buffer-after DURATION`                  | sec or ISO 8601 | `0`        | Extra video after scan end.                                                                                                 |
| `-p / --buffer-policy [strict\|flexible]`       | Choice          | `flexible` | Error or trim when buffers exceed video boundaries.                                                                         |
| `-t / --time-offset FLOAT`                      | seconds         | `0.0`      | Clock offset to add to `acq_time` values.                                                                                   |
| `-q / --qr [none\|auto\|embed-existing\|parse]` | Choice          | `none`     | QR code-based timing refinement mode (see QR Modes below).                                                                  |
| `-l / --layout [nearby\|top-stimuli]`           | Choice          | `nearby`   | Output file placement layout within the BIDS dataset (see Layout Modes below).                                              |
| `-z / --timezone TIMEZONE`                      | String          | `local`    | Timezone assumed for ReproStim naive timestamps (see Timezone Handling below).                                              |
| `-v / --verbose`                                | Flag            | False      | Increase verbosity.                                                                                                         |

### Example invocations

```shell
# Single _scans.tsv file
reprostim bids-inject \
  --videos sourcedata/reprostim-reproiner/videos.tsv \
  --buffer-before 10 --buffer-after 10 \
  --buffer-policy flexible \
  sourcedata/dbic-QA/sub-qa/ses-20250814/sub-qa_ses-20250814_scans.tsv

# Multiple _scans.tsv files in one run
reprostim bids-inject \
  --videos sourcedata/reprostim-reproiner/videos.tsv \
  sourcedata/dbic-QA/sub-qa/ses-20250814/sub-qa_ses-20250814_scans.tsv \
  sourcedata/dbic-QA/sub-qa/ses-20250901/sub-qa_ses-20250901_scans.tsv

# Session directory (finds all *_scans.tsv in that directory, non-recursive)
reprostim bids-inject \
  --videos sourcedata/reprostim-reproiner/videos.tsv \
  sourcedata/dbic-QA/sub-qa/ses-20250814/

# Entire dataset root, recursive (finds all *_scans.tsv anywhere below)
reprostim bids-inject \
  --videos sourcedata/reprostim-reproiner/videos.tsv \
  --recursive \
  sourcedata/dbic-QA/

# With clock offset correction
reprostim bids-inject \
  --videos /data/reprostim/videos.tsv \
  --time-offset -1.5 \
  sourcedata/dbic-QA/sub-qa/ses-20250814/sub-qa_ses-20250814_scans.tsv

# With QR-based timing refinement using pre-parsed QR data
reprostim bids-inject \
  --videos /data/reprostim/videos.tsv \
  --qr embed-existing \
  sourcedata/dbic-QA/sub-qa/ses-20250814/sub-qa_ses-20250814_scans.tsv

# Force ReproStim timestamps to a specific IANA timezone (e.g. scanner at Dartmouth = US Eastern)
reprostim bids-inject \
  --videos /data/reprostim/videos.tsv \
  --timezone America/New_York \
  sourcedata/dbic-QA/sub-qa/ses-20250814/sub-qa_ses-20250814_scans.tsv

# BIDS dataset uses UTC-aware acq_time; ReproStim captured in UTC (e.g. server clock set to UTC)
reprostim bids-inject \
  --videos /data/reprostim/videos.tsv \
  --timezone UTC \
  sourcedata/dbic-QA/sub-qa/ses-20250814/sub-qa_ses-20250814_scans.tsv
```

---

## QR Modes

The `--qr` option controls whether and how QR code data is used to refine timing alignment
beyond NTP-based synchronization (related to the future `bids-qr-sync` tool, issue #14):

| Mode             | Description                                                                                                               |
|------------------|---------------------------------------------------------------------------------------------------------------------------|
| `none`           | No QR processing. Timing is based solely on `acq_time` from `_scans.tsv` and `--time-offset`. Default.                    |
| `auto`           | Automatically detect and use QR data if available (parsed JSONL alongside video); fall back to NTP timing if not present. |
| `embed-existing` | Use pre-existing parsed QR JSONL files (produced by `qr-parse`) to refine timing. Error if JSONL not found.               |
| `parse`          | Run `qr-parse` on-the-fly against the source video to extract QR codes, then use results to refine timing.                |

QR-based refinement corrects for DICOM `AcquisitionTime` jitter (see issue #109) and
anonymization-induced time shifts by anchoring the video timeline to QR code timestamps
embedded during stimulus presentation.

---

## Layout Modes

The `--layout` option controls where the output `.mkv` and sidecar `.json` files are placed
relative to the BIDS dataset:

| Mode          | Description                                                                                                                                                                               |
|---------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `nearby`      | Output files are placed next to the corresponding NIfTI/sidecar in the same BIDS datatype folder (e.g. `sub-01/func/sub-01_task-rest_bold.mkv`). Default.                                |
| `top-stimuli` | Output files are placed under a top-level `stimuli/` directory in the BIDS root, mirroring the subject/session/datatype hierarchy (e.g. `stimuli/sub-01/func/sub-01_task-rest_bold.mkv`). |

---

## Timezone Handling

### Background

ReproStim records all timestamps (in `videos.tsv` columns `start_date`/`start_time`,
`end_date`/`end_time`) as **naive datetimes** — ISO 8601 strings with no UTC offset or
timezone designator. These timestamps reflect the wall-clock time of the capture machine and
implicitly represent the local timezone of the research site (e.g. US Eastern for Dartmouth).

BIDS `_scans.tsv` `acq_time` values may be:

- **Naive** (most common): no offset, implicitly local site time, e.g. `2025-08-14T15:06:09.742500`
- **UTC-aware**: explicit `+00:00` offset, e.g. `2025-08-14T20:06:09.742500+00:00`

Without consistent timezone treatment, naive ReproStim timestamps and UTC-aware BIDS timestamps
will be misaligned by the UTC offset of the site (e.g. 4–5 hours for US Eastern), causing all
video-to-scan matching to fail silently or produce wrong clips.

### The `--timezone` Option

`--timezone TIMEZONE` declares the timezone that should be assumed for **ReproStim's naive
timestamps**. Accepted values:

| Value                        | Meaning                                                                            |
|------------------------------|------------------------------------------------------------------------------------|
| `local` *(default)*          | Use the OS system timezone of the machine running `bids-inject`. Equivalent to `dateutil.tz.tzlocal()`. Appropriate when ReproStim and `bids-inject` run at the same site. |
| IANA timezone name           | Any name from the IANA tz database, e.g. `America/New_York`, `America/Chicago`, `UTC`, `Europe/London`. Use when running `bids-inject` on a machine in a different timezone than where the data was captured, or to be explicit and reproducible. |

> **Recommendation**: prefer an explicit IANA name (e.g. `America/New_York`) in scripts and
> workflows for reproducibility, even when `local` would give the same result. `local` is
> appropriate for interactive use at the capture site.

### Naive BIDS `acq_time` Handling

When a BIDS `acq_time` value carries no UTC offset, `bids-inject` assumes it is in the **same
timezone as `--timezone`**. This reflects the common case where both the DICOM exporter and
the ReproStim capture machine are on the same site clock.

If a BIDS `acq_time` already carries an explicit UTC offset (e.g. `+00:00`), it is used
as-is and converted to UTC for comparison; `--timezone` does not affect it.

### Normalization Algorithm

```
For each ReproStim timestamp t_rs (naive from videos.tsv):
    t_rs_aware = attach(t_rs, tz=resolve(--timezone))
    t_rs_utc   = t_rs_aware.astimezone(UTC)

For each BIDS acq_time t_bids:
    if t_bids has explicit UTC offset:
        t_bids_utc = t_bids.astimezone(UTC)
    else:  # naive — assume same site timezone
        t_bids_aware = attach(t_bids, tz=resolve(--timezone))
        t_bids_utc   = t_bids_aware.astimezone(UTC)

Match: find video where t_rs_utc(start) ≤ t_bids_utc < t_rs_utc(end)
```

All internal comparisons are performed in UTC. The `--time-offset` correction is applied
**after** timezone normalization, directly to `t_bids_utc`.

### Common Scenarios

| Scenario                                                           | Recommended invocation                        |
|--------------------------------------------------------------------|-----------------------------------------------|
| ReproStim + BIDS on same site, both naive (typical)                | *(omit `--timezone`, default `local` applies)* |
| Explicit reproducible script for US Eastern site                   | `--timezone America/New_York`                 |
| ReproStim machine clock set to UTC, BIDS naive timestamps in UTC   | `--timezone UTC`                              |
| Processing data from another site (different TZ than local machine)| `--timezone America/Chicago` (or site TZ)    |
| BIDS `acq_time` is UTC-aware (`+00:00`), ReproStim is US Eastern   | `--timezone America/New_York`                 |

---

## Algorithm / Data Flow

```
1. Load videos.tsv (from --videos)
   └─ Build index: (date, time_range) → video file path
      (paths resolved relative to videos.tsv location)
      Resolve --timezone → tz object (tzlocal() for "local", or IANA lookup)
      Attach tz to all naive start/end timestamps; convert to UTC

2. For each subject/session in BIDS_ROOT:
   a. Load <sub>/<ses>/*_scans.tsv
   b. For each scan row:
      i.  Parse acq_time → normalize to UTC (see Timezone Handling):
            - naive: attach --timezone, convert to UTC
            - aware: convert to UTC directly
          Apply --time-offset (seconds) to UTC-normalized acq_time
      ii. Determine scan duration:
            - From *_bold.json → FrameAcquisitionDuration (preferred)
            - OR compute from AcquisitionTime array length × TR
            - OR from RepetitionTime × NumberOfVolumes
            - Fallback: error / warn and skip
      iii. Resolve matching video from videos.tsv index
            - Must overlap [start, start+duration]
            - If multiple matches: error (multi-video case not supported yet)
            - If no match: warn and skip
      iv.  (If --qr != none) Refine timing using QR data:
            - auto: use JSONL if present, else skip refinement
            - embed-existing: load JSONL; error if missing
            - parse: invoke qr-parse on source video, then load results
            - Apply QR-derived offset to start/duration
      v.   Determine output path (per --layout):
              nearby:       <bids_root>/<sub>[/<ses>]/<datatype>/<bids_basename>.mkv
              top-stimuli:  <bids_root>/stimuli/<sub>[/<ses>]/<datatype>/<bids_basename>.mkv
      vi.  Call split-video:
              TODO: use -spec and templated output path if any for batch processing
                    also use direct invocation of split-video API instead of CLI for
                    better error handling
              split-video \
                --start <acq_time+offset> --duration <scan_duration> \
                --buffer-before <N> --buffer-after <N> \
                --buffer-policy <policy> \
                --sidecar-json \
                --input <video_path> --output <output_mkv>

3. Report summary: N injected, M skipped, K errors
```

---

## Duration Computation

Priority order for determining scan duration from BIDS JSON sidecars:

1. ??? TODO: Check `FrameAcquisitionDuration` (ms → seconds) — *most reliable*
2. `AcquisitionTime` array → `last_time - first_time + TR`.  The acq_duration of video is
pretty much from that AcquisitionTime array ([-1] - [0]) + ([1] - [0])
3. `RepetitionTime` (s) × `NumberOfVolumes`
4. ?? TODO: think about manual override via future `--duration` option

Anatomical scans not used to split videos at this moment, only functional scans.

### Manual Inspection

Functional scan metadata can be checked manually using `nib-ls`:

```shell
nib-ls sub-qa_ses-20250814_acq-faX77_bold.nii.gz
```

Example output:
```
int16 [ 80,  80,  30,   3] 3.00x3.00x3.99x2.00   sform
```

The fields are: `dtype [X, Y, Z, N_volumes] vx_size_x x vx_size_y x vx_size_z x TR_sec`.
In this example: 3 volumes × TR 2.00 s = **6.0 s** total scan duration.

---

## _scans.tsv Integration

The BIDS `_scans.tsv` file lists all acquisitions for a given subject/session. Example:

```shell
cat sub-qa_ses-20250814_scans.tsv
```
```
filename                                                                        acq_time                    operator    randstr
func/sub-qa_ses-20250814_task-rest_acq-p2_bold__dup-01.nii.gz                  2025-08-14T15:06:09.742500  n/a         77b0dbb6
func/sub-qa_ses-20250814_task-rest_acq-p2Xs4X35mm_bold.nii.gz                  2025-08-14T15:13:03.985000  n/a         47dccded
func/sub-qa_ses-20250814_acq-faX77_bold.nii.gz                                 2025-08-14T15:19:53.397500  n/a         6b371aad
func/sub-qa_ses-20250814_task-rest_acq-p2_bold.nii.gz                          2025-08-14T15:25:30.500000  n/a         8a68d233
```

The two columns used by `bids-inject`:

| Column       | Usage                                                                                                                                                                                     |
|--------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `filename`   | Relative path to the NIfTI file within the subject/session directory. Used to derive the output `.mkv` basename and locate the corresponding DICOM JSON sidecar for duration computation. |
| `acq_time`   | ISO 8601 datetime of scan acquisition start. Combined with `--time-offset`, this is matched against the `start_time`/`end_time` range in `videos.tsv` to find the covering video file.    |

Other columns (`operator`, `randstr`, etc.) are ignored.

**Filtering rules** — a scan row is processed only if both conditions are met:

1. `filename` starts with `func/` — only functional scans are considered; anatomical and other
   datatypes are skipped.
2. The corresponding NIfTI file has **2 or more volumes** (4th dimension ≥ 2, as reported by
   `nib-ls` or the JSON sidecar). Single-volume acquisitions are skipped.

---

## videos.tsv Integration

Columns used by `bids-inject`:

| Column                     | Usage                                                            |
|----------------------------|------------------------------------------------------------------|
| `path`                     | Path to `.mkv` file (resolved relative to `videos.tsv` location) |
| `present`                  | Must be `True`; skip if `False`                                  |
| `complete`                 | Prefer `True`; warn if `False`                                   |
| `start_date`, `start_time` | Combined → video start datetime                                  |
| `end_date`, `end_time`     | Combined → video end datetime                                    |
| `duration`                 | Total duration in seconds (sanity check)                         |

---

## File / Module Structure

| File                                     | Purpose                                                     |
|------------------------------------------|-------------------------------------------------------------|
| `src/reprostim/cli/cmd_bids_inject.py`   | Click command definition (`bids-inject`)                    |
| `src/reprostim/qr/bids_inject.py`        | Core logic: TSV loading, duration resolution, orchestration |

Registered in `src/reprostim/cli/entrypoint.py` alongside other commands.

---

## Dependencies / Related Components

| Component       | Relationship                                               |
|-----------------|------------------------------------------------------------|
| `split-video`   | Called by `bids-inject` to do actual video slicing         |
| `video-audit`   | Produces `videos.tsv` consumed by `bids-inject`            |
| `qr-parse`      | Invoked by `bids-inject` when `--qr parse` mode is used    |
| Issue #13       | Clock synchronization / offset tracking (`--time-offset`)  |
| Issue #83       | Metadata JSON logging spec (sidecar schema)                |
| Issue #109      | DICOM `AcquisitionTime` jitter documentation               |
| BEP044/BEP047   | BIDS Enhancement Proposals for stimuli and behavioral data |

---

## Error Handling

| Condition                               | Behavior                                    |
|-----------------------------------------|---------------------------------------------|
| No matching video for a scan            | Warn and skip                               |
| Multiple overlapping videos             | Error and skip that scan                    |
| Incomplete/truncated video              | Warn; attempt if `--buffer-policy flexible` |
| Cannot determine scan duration          | Error and skip                              |
| `--qr embed-existing` and JSONL missing | Error and skip that scan                    |
| `videos.tsv` not found                  | Fatal error                                 |
| `_scans.tsv` not found                  | Warn and skip subject/session               |

---

## Open Questions / TODOs

1. **Multi-video case**: If a scan spans two capture files, currently errors. Future: join/concat, think about data loss/integrity.
2. **`bids-qr-sync` integration**: Future tool to refine timing via QR codes; `--qr` modes lay the groundwork.
3. **Anonymized datasets**: `--time-offset` addresses shifted DICOM times but calibration is manual.
4. **BIDS column naming**: Confirm sidecar buffer field names against BEP044/BEP047.
5. **DataLad integration**: Consider auto-adding output `.mkv` files to BIDS DataLad dataset.
6. **Testing**: Need test datasets with known video-scan alignments to validate functionality.
7. **Strict Timing Mode**: In future integrate existing time sync calibration data and `tmaps` to better handle timing ( as future development and grows of [reproflow-data-sync prototype](https://github.com/ReproNim/reproflow-data-sync)).
8. **_events.tsv** metadata like `sub-qa_ses-20250814_acq-faX77_recording-reprostim_events.tsv` with all the qr codes we parse in BIDS compliant form.
9. **filter** option: if to process .tsv files, should get a regex to select only some files (e.g. only func/) and default to all
10. **Timezone handling**: ReproStim based timestamps are always in local time (TZ-neutral but implicitly in timezone of research center); BIDS `acq_time` is often in UTC. Need to ensure consistent timezone handling when matching.
11. **Parallel processing**: The natural parallelism granularity is one `_scans.tsv` per worker (scans within a session stay sequential). When multiple sessions run concurrently, shared output data (summary counters, QR JSONL cache, any merged report files) will need lock protection. To be designed when a `--jobs` option is introduced.
