# BIDS Inject Sidecar Tool Specification

## Overview

`bids-inject-sidecar` is a standalone, low-level CLI command that extracts BIDS media-file
metadata (per the [BEP044/media-files proposal, bids-standard/bids-specification PR
#2367](https://bids-specification--2367.org.readthedocs.build/en/2367/appendices/media-files.html))
directly from one or more audio and/or video files and writes/updates the corresponding
`.json` sidecar file(s) next to each input file.

Unlike [`bids-inject`](spec-bids-inject.md), this command does **not** perform scan-matching,
timing orchestration, or `_scans.tsv` I/O. It operates purely file-by-file: given a media file,
it produces (or updates) its sidecar. It is meant to become the generic "engine" that
`bids-inject` delegates to for sidecar generation, replacing the inline `_to_bids_model` /
`_write_sidecar` logic currently embedded in `split_video.py` (see
[Relationship to `bids-inject` / `split-video`](#relationship-to-bids-inject--split-video)).

Corresponds to GitHub issue: https://github.com/ReproNim/reprostim/issues/259
Relevant to: https://github.com/ReproNim/reprostim/issues/14

---

## Motivation

`split-video` and `bids-inject` already write BEP044/047-style sidecars, but only as a side
effect of the video-slicing pipeline, and only for files they themselves produce. There is no
standalone tool to:

- (Re)generate or refresh a sidecar for a media file that already exists on disk (e.g. one not
  produced by `split-video`, or produced before certain metadata fields existed).
- Merge hand-supplied metadata (`DeviceSerialNumber`, `RecordingDuration`, etc.) into an existing
  sidecar without clobbering unrelated fields.
- Safely re-run metadata extraction against a batch of files with clear conflict-handling rules
  when a field's value changes between runs.

`bids-inject-sidecar` fills this gap as a focused, composable primitive that other tools
(`bids-inject`, ad-hoc scripts, QA pipelines) can shell out to or import.

---

## Scope

**In scope** (this issue):
- Audio and video files only.
- Extracting technical stream metadata via `ffprobe`.
- Merging in user-supplied `--add` field values, with type casting for known BIDS fields.
- `replace` vs `update` sidecar-writing modes.
- Conflict handling when a field's new value differs from an existing sidecar value.

**Out of scope** (explicitly deferred per issue #259):
- **Image files** (`_image` suffix / JPEG, PNG, SVG, WebP, TIFF per BEP044). Only audio/video are
  handled now; image support is future work.
- **Preserving original JSON formatting/ordering** when updating an existing sidecar. Minimizing
  diffs on update is non-trivial; the issue suggests evaluating/contributing to
  [bids-utils](https://github.com/bids-standard/bids-utils/) for this in a future iteration.
  For now, `update` mode may rewrite the file with standard `json.dumps(..., indent=2)`
  formatting, not preserving the original file's whitespace/key order beyond what's noted in
  [JSON Sidecar Write Behavior](#json-sidecar-write-behavior).

---

## CLI Interface

```
reprostim bids-inject-sidecar [OPTIONS] FILE1 [FILE2 ...]
```

### Arguments

| Argument       | Description                                                                                          |
|----------------|--------------------------------------------------------------------------------------------------------|
| `FILE1 [FILE2 ...]` | One or more paths to audio and/or video files to process. At least one file is required. Each file is processed independently; a `.json` sidecar is written/updated next to each. |

### Options

| Option                                       | Type    | Default   | Description                                                                                                                                                                                     |
|-----------------------------------------------|---------|-----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `-f / --videos PATH`                     | Path    | none      | Optional path to a `videos.tsv` (produced by `video-audit`). When given, cached fields (`audio_sr`, `video_res_detected`, codec info) are looked up for each `FILE` by resolved path and reused instead of re-running `ffprobe`. Falls back to `ffprobe` for any file not found in the TSV, or for fields the TSV doesn't carry. |
| `--json-mode [replace\|update]`               | Choice  | `update`  | `replace` overwrites the entire sidecar `.json` with only the freshly extracted/`--add`ed fields. `update` merges freshly extracted/`--add`ed fields into the existing sidecar (if any), preserving other existing keys untouched. See [JSON Sidecar Write Behavior](#json-sidecar-write-behavior). |
| `--add META=VALUE`                            | String, repeatable | none | Manually specify (or override) a metadata field, e.g. `--add DeviceSerialNumber=ABC12345 --add RecordingDuration=3600`. If `META` is a known BIDS media-file field (see [BIDS Media-File Metadata Fields](#bids-media-file-metadata-fields)), `VALUE` is cast to that field's declared type. Unknown fields are stored verbatim as strings. Repeatable — pass once per field. |
| `--existing-different [error\|overwrite]`     | Choice  | `error`   | Policy when a field about to be written already exists in the sidecar with a **different, non-`n/a`** value. `error`: abort processing that file and report the conflict. `overwrite`: log a warning and proceed with the new value. See [Conflict Resolution](#conflict-resolution). |
| `-v / --verbose`                              | Flag    | `False`   | Increase verbosity (per-field extraction/merge/conflict detail).                                                                                                                                |
| `-d / --dry-run`                              | Flag    | `False`   | *(Added for consistency with `bids-inject`/`video-audit`; not explicitly requested in issue #259.)* Compute and print the field set that would be written per file, without writing any sidecar. |

> **Note on additions beyond the issue text:** `-v/--verbose` and `-d/--dry-run` were added to
> match the conventions of every other `reprostim` subcommand (see [spec-bids-inject.md](spec-bids-inject.md),
> [spec-video-audit.md](spec-video-audit.md)). They are not present in the original issue body
> and can be dropped if deemed unnecessary during implementation review.

### Example invocations

```shell
# Extract + write a fresh sidecar for a single file (update mode, default)
reprostim bids-inject-sidecar sub-01_task-rest_recording-reprostim_audiovideo.mkv

# Batch: process every recording in a session directory
reprostim bids-inject-sidecar sub-01/ses-01/func/*_recording-reprostim_*.mkv

# Reuse cached video-audit metadata instead of re-running ffprobe
reprostim bids-inject-sidecar --videos sourcedata/reprostim-reproiner/videos.tsv \
  sub-01/ses-01/func/sub-01_ses-01_recording-reprostim_audiovideo.mkv

# Manually add/override fields not derivable from ffprobe
reprostim bids-inject-sidecar \
  --add DeviceSerialNumber=ABC12345 \
  --add RecordingDuration=3600 \
  sub-01_task-rest_recording-reprostim_audiovideo.mkv

# Replace the sidecar entirely instead of merging
reprostim bids-inject-sidecar --json-mode replace sub-01_task-rest_recording-reprostim_video.mkv

# Allow overwriting a differing existing value (logs a warning per field)
reprostim bids-inject-sidecar --existing-different overwrite \
  --add DeviceSerialNumber=NEWSERIAL01 \
  sub-01_task-rest_recording-reprostim_audiovideo.mkv

# Dry-run: see what would be written without touching any file
reprostim bids-inject-sidecar --dry-run sub-01/ses-01/func/*_recording-reprostim_*.mkv
```

---

## BIDS Media-File Metadata Fields

Field names, types, and descriptions per BEP044 (media-files proposal, PR #2367). Used both to
know which `--add META=...` keys should be type-cast, and as the set of fields `ffprobe`
extraction populates.

| Field                | Type    | Applies to    | Description                                              |
|-----------------------|---------|----------------|------------------------------------------------------------|
| `RecordingDuration`   | number  | audio/video/image | Length of the recording in seconds.                    |
| `AudioCodec`          | string  | audio/audiovideo | FFmpeg codec name (e.g. `"aac"`, `"mp3"`, `"opus"`).     |
| `AudioSampleRate`     | number  | audio/audiovideo | Sampling frequency of the audio stream, in Hz.           |
| `AudioChannelCount`   | integer | audio/audiovideo | Number of audio channels.                                |
| `AudioBitDepth`       | integer | audio/audiovideo | Bits per sample (typically uncompressed/lossless audio). |
| `AudioCodecRFC6381`   | string  | audio/audiovideo | RFC 6381 codec string.                                    |
| `ImageWidth`          | integer | video/image    | Width of the video frame or image, in pixels.               |
| `ImageHeight`         | integer | video/image    | Height of the video frame or image, in pixels.               |
| `ImagePixelFormat`    | string  | video/image    | FFmpeg `pix_fmt` value (e.g. `"yuv420p"`).                   |
| `ImageBitDepth`       | integer | video/image    | Bit depth per channel of the stored pixel data.              |
| `VideoCodec`          | string  | video/audiovideo | FFmpeg codec name (e.g. `"h264"`, `"hevc"`, `"vp9"`).    |
| `VideoFrameRate`      | number  | video/audiovideo | Video frame rate of the video stream, in Hz.              |
| `VideoFrameCount`     | integer | video/audiovideo | Total number of frames in the video stream.               |
| `VideoCodecRFC6381`   | string  | video/audiovideo | RFC 6381 codec string.                                     |
| `Device`              | string  | any            | Capture device name. *(ReproStim extra, not in BEP044.)*    |
| `DeviceSerialNumber`  | string  | any            | Capture device serial number. *(ReproStim extra.)*          |
| `TaskName`             | string  | any            | BIDS task name, when applicable.                            |

Any `--add META=VALUE` key not in this table is treated as an opaque extra field and stored as
a plain string (no casting attempted).

> **Reconciliation needed with `bids-inject`:** `split_video.py`'s existing `_to_bids_model`
> writes `Width` / `Height` / `PixelFormat` / `BitDepth` — **not** the `Image*`-prefixed names
> shown above. This mismatch predates this spec (tracked as item 4 in
> [spec-bids-inject.md § Open Questions](spec-bids-inject.md#open-questions--todos)). This tool
> should use the correct `Image*`-prefixed names per the current BEP044 draft; reconciling
> `split_video.py`'s field names is tracked as follow-up work (see
> [Relationship to `bids-inject` / `split-video`](#relationship-to-bids-inject--split-video)).

---

## Field Extraction

For each input `FILE`, technical metadata is obtained in this priority order:

1. **`--videos` cache lookup** (if `-f/--videos` given): resolve `FILE`'s path the same
   way `bids-inject` resolves video paths relative to `videos.tsv`'s location, and look for a
   matching `VaRecord` row. If found, map its `audio_sr`, `video_res_detected`, and any recorded
   codec columns into the BIDS field table above.
2. **`ffprobe` extraction** (fallback, or when `--videos` is omitted): call
   `get_audio_video_info_ffprobe(path)` (reused from `src/reprostim/qr/video_audit.py`) to obtain
   `AudioInfo` / `VideoInfo`, then map their fields into the BIDS field table above. Any field the
   cache lookup didn't supply is filled from here.
3. **`--add META=VALUE` overrides** (highest priority): applied last, after extraction, so
   manually-specified values always take precedence over extracted ones for the same key
   (subject to [Conflict Resolution](#conflict-resolution) against a pre-existing sidecar value).

Fields that cannot be determined (no matching stream, `ffprobe` failure) are simply omitted from
the written sidecar rather than written as `"n/a"` placeholders — a sidecar field with no value
is absent, not `n/a`. (`"n/a"` is only used internally to represent "no existing sidecar value"
when evaluating conflicts, matching the `videos.tsv` / `_scans.tsv` convention used elsewhere in
this codebase.)

---

## JSON Sidecar Write Behavior

### Sidecar path resolution

The sidecar path is the input file path with its extension replaced by `.json`:

```
sub-01_task-rest_recording-reprostim_audiovideo.mkv
  → sub-01_task-rest_recording-reprostim_audiovideo.json
```

### `--json-mode`

| Mode      | Behaviour                                                                                                                                                     |
|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `update`  | **(default)** Load existing sidecar JSON if present (empty dict if not). Merge in newly extracted / `--add`ed fields per [Conflict Resolution](#conflict-resolution). All pre-existing keys not touched by this run are preserved as-is. Write the merged result back with `json.dumps(..., indent=2)`. |
| `replace` | Existing sidecar content (if any) is discarded entirely. Write a fresh sidecar containing only the fields produced by this run (extraction + `--add`).            |

### Conflict Resolution

Applies to every field about to be written, whether from extraction or `--add`, when a sidecar
already exists (`update` mode only — `replace` mode has no prior content to conflict with):

| Existing value | New value | Outcome                                                                                     |
|----------------|-----------|-----------------------------------------------------------------------------------------------|
| absent / not present | any  | Write it. No conflict.                                                                        |
| `n/a` (or explicit "no value") | any real value | Write it. Treated as no prior value — never a conflict.                              |
| same as new value | same     | No-op (already correct); not counted as a conflict.                                          |
| real, non-`n/a` value | different real value | `--existing-different error` (default): abort that file, report the conflicting field/values, do not write. `--existing-different overwrite`: log a warning, write the new value. |
| real, non-`n/a` value | `n/a`    | Treated as a "different value" case above — **`error` is the default outcome regardless of `--existing-different`**, since downgrading a real value to no-value is never silently safe. `--existing-different overwrite` still logs+proceeds if the caller explicitly opts in. |

`--add`-supplied values are subject to the exact same rules as extracted values — there is no
separate bypass for manually-supplied fields.

On `error`, the file is skipped (counted as an error) and processing continues with the next
`FILE` in the batch; the command's overall exit code is non-zero if any file errored.

---

## `--add` Value Casting

For each `--add META=VALUE`:

1. If `META` matches a name in the [BIDS Media-File Metadata Fields](#bids-media-file-metadata-fields)
   table, cast `VALUE` to the declared type:
   - `integer` → `int(VALUE)`
   - `number` → `float(VALUE)`
   - `string` → used as-is
   - Casting failure (e.g. `--add AudioChannelCount=stereo`) → error, file skipped, reported like
     any other per-file error.
2. Otherwise, `META` is stored verbatim as a string — no attempt to guess int/float.

---

## Algorithm / Data Flow

```
1. Parse --add META=VALUE pairs into a dict, casting known fields per BIDS Media-File
   Metadata Fields table; error out early (before touching any file) on a casting failure
   in a --add value, since it applies identically to every file in the batch.

2. If --videos given: load videos.tsv once (cached), build a path → VaRecord index
   (paths resolved relative to videos.tsv location, matching bids-inject's convention).

3. For each FILE in FILE1 [FILE2 ...]:
   a. Resolve sidecar path: FILE with extension replaced by ".json".
   b. Determine existing sidecar content:
        - update mode: load JSON if sidecar exists, else {}
        - replace mode: {} (existing content discarded, only used for logging what
          was overwritten in --verbose)
   c. Extract technical fields:
        i.  Look up FILE in the videos.tsv index (if loaded); map matched columns.
        ii. For any BIDS field not yet populated, run ffprobe via
            get_audio_video_info_ffprobe(FILE) and map AudioInfo/VideoInfo → BIDS fields.
   d. Apply --add overrides on top of extracted fields (highest priority).
   e. For each field to be written, apply Conflict Resolution against the existing
      sidecar content (update mode only). On an unresolved conflict (error mode),
      mark this FILE as errored and stop processing it (no partial write).
   f. If --dry-run: print the field set that would be written; do not write.
      Else: write merged/replaced JSON to the sidecar path (json.dumps(..., indent=2)).

4. Report summary: N processed, M written, K errors. Non-zero exit code if K > 0.
```

---

## File / Module Structure

| File                                              | Purpose                                                                 |
|----------------------------------------------------|--------------------------------------------------------------------------|
| `src/reprostim/cli/cmd_bids_inject_sidecar.py`      | Click command definition (`bids-inject-sidecar`)                       |
| `src/reprostim/qr/bids_inject_sidecar.py`           | Core logic: per-file extraction, `--add` casting, conflict resolution, JSON read/write |
| `src/reprostim/qr/bids_media.py` *(proposed, new)*  | Shared BIDS media-field table + `AudioInfo`/`VideoInfo` → BIDS-dict mapping, factored out of `split_video.py`'s `_to_bids_model` so both `split-video`/`bids-inject` and `bids-inject-sidecar` use one source of truth for field names/types. |

Registered in `src/reprostim/cli/entrypoint.py` alongside other commands.

---

## Relationship to `bids-inject` / `split-video`

`split_video.py` already contains `_to_bids_model()` and `_write_sidecar()`, used by
`split-video --sidecar-json` and, transitively, by `bids-inject` (see
[spec-bids-inject.md § Outputs → B](spec-bids-inject.md#b-sidecar-metadata--bep047behavior--reprostim-extras)).
That existing logic is narrower in scope: it only ever writes a **fresh** sidecar for a file
`split-video` itself just produced, with no notion of merging into or reconciling against a
pre-existing sidecar.

`bids-inject-sidecar` is the generalization of that logic to arbitrary existing files, with
explicit merge/conflict semantics. Recommended (but out of scope for the initial
`bids-inject-sidecar` implementation) follow-up work:

1. Extract the BIDS field-name/type table and `AudioInfo`/`VideoInfo` → BIDS-dict mapping out of
   `split_video.py::_to_bids_model` into the shared `bids_media.py` module proposed above.
2. Reconcile the `Width`/`Height`/`PixelFormat`/`BitDepth` vs `ImageWidth`/`ImageHeight`/
   `ImagePixelFormat`/`ImageBitDepth` naming mismatch (see
   [BIDS Media-File Metadata Fields](#bids-media-file-metadata-fields) note above) in one place.
3. Have `split_video.py::_write_sidecar` optionally delegate to `bids-inject-sidecar`'s
   `update`-mode writer instead of its own `_write_sidecar`, once the merge semantics are proven.

---

## Dependencies / Related Components

| Component                       | Relationship                                                                 |
|----------------------------------|-------------------------------------------------------------------------------|
| `get_audio_video_info_ffprobe`   | Reused from `src/reprostim/qr/video_audit.py` for ffprobe-based extraction.  |
| `videos.tsv` / `video-audit`     | Optional metadata cache source via `--videos`, avoiding redundant `ffprobe` calls. |
| `bids-inject`                    | Prospective consumer — see [Relationship](#relationship-to-bids-inject--split-video). |
| `split-video`                    | Prospective consumer of the same writer logic for `--sidecar-json`.          |
| [bids-utils](https://github.com/bids-standard/bids-utils/) | Candidate library for format-preserving JSON updates (future work, out of scope now). |
| Issue #14                        | Parent BIDS-integration effort this tool supports.                           |
| BEP044/media-files (PR #2367)    | Source of the metadata field names/types used here.                          |

---

## Error Handling

| Condition                                                  | Behavior                                                                 |
|--------------------------------------------------------------|-----------------------------------------------------------------------------|
| Input `FILE` does not exist                                 | Error and skip that file; continue with the rest of the batch.             |
| `ffprobe` not installed / fails                              | Error logged (per existing `get_audio_video_info_ffprobe` behavior); fields it would have supplied are simply omitted, not fatal to the whole file unless no fields at all could be determined and no `--add` compensates. |
| `--videos` given but path not found in `videos.tsv`     | Fall back to `ffprobe` extraction for that file; not an error.             |
| Malformed `--add META=VALUE` (missing `=`)                    | Fatal error before any file is processed (applies to whole invocation).    |
| `--add` value fails type casting for a known BIDS field       | Fatal error before any file is processed.                                  |
| Existing sidecar JSON is not valid JSON (`update` mode)        | Error and skip that file; do not attempt a partial merge.                  |
| Field conflict, `--existing-different error` (default)         | Error and skip that file; report the conflicting field, old and new values.|
| Field conflict, `--existing-different overwrite`                | Warn and proceed; value is overwritten.                                    |
| Sidecar directory not writable                                 | Error and skip that file.                                                  |

---

## Open Questions / TODOs

1. **Image file support** — explicitly deferred per issue #259; would need the `Image*` fields
   above plus non-audio/video decode handling (e.g. Pillow/`ffprobe` for stills).
2. **Format-preserving JSON updates** — evaluate/contribute to
   [bids-utils](https://github.com/bids-standard/bids-utils/) so `update` mode can minimize diffs
   against hand-edited sidecars instead of rewriting with `json.dumps`.
3. **Shared `bids_media.py` extraction** — factor `_to_bids_model`'s field mapping out of
   `split_video.py` so `bids-inject`/`split-video` and `bids-inject-sidecar` share one source of
   truth (see [Relationship](#relationship-to-bids-inject--split-video)).
4. **Field naming reconciliation** — `Width`/`Height`/`PixelFormat`/`BitDepth` (current
   `split_video.py`) vs `ImageWidth`/`ImageHeight`/`ImagePixelFormat`/`ImageBitDepth` (current
   BEP044 draft used by this spec). Needs a single decision applied everywhere.
5. **`--videos` path-matching precision** — exact resolved-path match vs. the time-range
   matching `bids-inject` uses (`find_video_audit_by_timerange`); a plain path match is proposed
   here since `bids-inject-sidecar` operates on files directly rather than matching against scan
   timing windows.
6. **`--dry-run` / `-v` options** — added for consistency with sibling commands; confirm desired
   before implementation, since they are not in the original issue text.
7. **Casting failures for unknown-but-numeric-looking `--add` fields** — currently no casting is
   attempted for fields outside the BIDS table; revisit if users expect e.g. `--add
   CustomCount=5` to become an int.
