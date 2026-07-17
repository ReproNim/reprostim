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

**Status: basic per-file extraction/write logic implemented** — `ffprobe`-based extraction (via
`bids_properties_from_ffprobe`), `--videos`/`videos.tsv` cache lookup (via
`bids_properties_from_video_audit`, falling back to `ffprobe` when there's no cache or no
matching row), `--add` merge, `update`/`replace` write modes, and `error`/`overwrite` conflict
resolution all work end-to-end. **Not yet implemented**: `--add` declared-type casting. See
[task-bids-inject-sidecar.md](task-bids-inject-sidecar.md) for the detailed checklist.

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
| `-f / --videos PATH`                     | Path    | none      | Optional path to a `videos.tsv` (produced by `video-audit`). When given, `bids_properties_from_video_audit` looks up a cached `VaRecord` for each `FILE` (via `get_file_video_audit(..., cached=True, use_lock=False)`) and maps its `duration`/`video_res_recorded`/`video_fps_recorded`/`audio_sr` fields (plus `Device`/`DeviceSerialNumber` recovered from `<FILE>.log`, and `VideoCodec` inferred as `"h264"`) instead of re-running `ffprobe`. Falls back to `ffprobe` if the file has no matching row in the TSV, or if the lookup itself raises. |
| `-m / --mode [replace\|update]`               | Choice  | `update`  | `replace` overwrites the entire sidecar `.json` with only the freshly extracted/`--add`ed fields. `update` merges freshly extracted/`--add`ed fields into the existing sidecar (if any), preserving other existing keys untouched. See [JSON Sidecar Write Behavior](#json-sidecar-write-behavior). |
| `-a / --add META=VALUE`                       | String, repeatable | none | Manually specify (or override) a metadata field, e.g. `--add DeviceSerialNumber=ABC12345 --add RecordingDuration=3600`, or supply several at once as a bare JSON object, e.g. `--add '{"AudioCodec": "aac", "AudioSampleRate": 48000}'`. `VALUE` is parsed as JSON when possible (so numbers/bools/`null`/objects come through typed), else stored as a plain string. See [`--add` Value Parsing](#--add-value-parsing-implemented-_parse_ext_props). Repeatable — entries merge in order, later keys win on conflict. |
| `-e / --existing-different [error\|overwrite]` | Choice  | `error`   | Policy when a field about to be written already exists in the sidecar with a **different, non-`n/a`** value. `error`: abort processing that file and report the conflict. `overwrite`: log a warning and proceed with the new value. See [Conflict Resolution](#conflict-resolution). |
| `-s / --strict`                               | Flag    | `False`   | When set, a `FILE` failing the `parse_bids_media_info` validity check (`bmi.valid is False`) is a fatal error for that file — reported via `_error` and the file is skipped. When not set (default), the same problem is only reported as a warning (`_warn`) and processing continues to extraction/write for that file. |
| `-v / --verbose`                              | Flag    | `False`   | Increase verbosity (per-field extraction/merge/conflict detail).                                                                                                                                |
| `-d / --dry-run`                              | Flag    | `False`   | *(Added for consistency with `bids-inject`/`video-audit`; not explicitly requested in issue #259.)* Compute and print the field set that would be written per file, without writing any sidecar. |

> **Note on additions beyond the issue text:** `-v/--verbose` and `-d/--dry-run` were added to
> match the conventions of every other `reprostim` subcommand (see [spec-bids-inject.md](spec-bids-inject.md),
> [spec-video-audit.md](spec-video-audit.md)). They are not present in the original issue body
> and can be dropped if deemed unnecessary during implementation review.

> **Enum types (implemented):** `--mode` is backed by `OverwriteMode(str, Enum)`
> (`REPLACE`/`UPDATE`) and `--existing-different` by `ConflictPolicy(str, Enum)`
> (`ERROR`/`OVERWRITE`), both defined in `inject_sidecar.py` itself — scoped to this command only,
> not shared with `bids/inject.py`'s own (differently-scoped) `OverwriteMode` enum (existing-file
> overwrite policy for `bids-inject`, values `SKIP`/`FORCE`/`ALWAYS`/`ERROR`). The two classes are
> intentionally same-named but distinct, disambiguated by module (`reprostim.bids.inject.OverwriteMode`
> vs. `reprostim.bids.inject_sidecar.OverwriteMode`). `BisContext` carries them as `mode` and
> `conflict_policy` fields, alongside `videos_tsv`, `strict`, `dry_run`, `verbose`, and `out_func`
> (all populated directly from `do_main`'s corresponding parameters — same field names/style as
> `bids/inject.py::BiContext`).

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
reprostim bids-inject-sidecar --mode replace sub-01_task-rest_recording-reprostim_video.mkv

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

> **Naming status: fully migrated to `Image*`-prefixed BEP044 names.** The BEP044
> (media-files, PR #2367) draft specifies `ImageWidth` / `ImageHeight` / `ImagePixelFormat` /
> `ImageBitDepth`. `bids/properties.py::bids_properties_from_split_result` (used by
> `split-video`/`bids-inject` via `split_video.py::_write_sidecar`; this logic used to live
> directly in `split_video.py` as `_to_bids_model`, moved out — see
> [spec-bids-properties.md](spec-bids-properties.md)) writes all four `Image*`-prefixed names —
> `ImagePixelFormat`/`ImageBitDepth` were renamed first (coordinated with `bids/inject.py`
> switching to `bids/properties.py::bids_properties_from_ffprobe`), and `ImageWidth`/
> `ImageHeight` (from `SplitResult.video_width`/`video_height`) followed in a second pass. Every
> key in this table that has a matching [`BidsMediaProperty`](spec-bids-media.md) member is
> written via `BidsMediaProperty.*.value`, not a raw string literal — see
> [Relationship to `bids-inject` / `split-video`](#relationship-to-bids-inject--split-video).

---

## Field Extraction

For each input `FILE`, technical metadata is obtained in this priority order:

1. **`--videos` cache lookup** (if `-f/--videos` given): `bids_properties_from_video_audit(path,
   path_tsv)` calls `get_file_video_audit(path, path_tsv, cached=True, use_lock=False)` to resolve
   `FILE` against the `videos.tsv` index and look for a matching `VaRecord` row. If found, maps
   its `duration`/`video_res_recorded`/`video_fps_recorded`/`audio_sr` fields into the BIDS field
   table above, plus `Device`/`DeviceSerialNumber` (recovered from a `session_begin`
   REPROSTIM-METADATA-JSON entry in `<FILE>.log`) and `VideoCodec` (inferred as `"h264"` whenever
   `video_res_recorded` is present). If `bids_properties_from_video_audit` raises, `_do_sidecar`
   falls back to step 2 for that file.
2. **`ffprobe` extraction** (fallback, or when `--videos` is omitted): call
   `bids_properties_from_ffprobe(path)` (wraps `get_audio_video_info_ffprobe`, reused from
   `src/reprostim/qr/video_audit.py`) to obtain `AudioInfo` / `VideoInfo`, then map their fields
   into the BIDS field table above. Used instead of step 1's result entirely for a given file
   (not merged field-by-field) — `_do_sidecar` picks one source or the other per file.
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

### `--mode`

| Mode      | Behaviour                                                                                                                                                     |
|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `update`  | **(default)** Load existing sidecar JSON if present (empty dict if not). Merge in newly extracted / `--add`ed fields per [Conflict Resolution](#conflict-resolution). All pre-existing keys not touched by this run are preserved as-is. Write the merged result back with `json.dumps(..., indent=2)`. |
| `replace` | Existing sidecar content (if any) is discarded entirely. Write a fresh sidecar containing only the fields produced by this run (extraction + `--add`).            |

### Conflict Resolution (implemented)

Applies to every field about to be written, whether from extraction or `--add`, when a sidecar
already exists (`update` mode only — `replace` mode has no prior content to conflict with).
`_do_sidecar`'s conflict-resolution loop implements this table exactly, including the "real vs.
`n/a`" row, without needing a special case for it (falls naturally into the general
"differs" branch, which is already policy-driven):

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

## `--add` Value Parsing (implemented: `_parse_ext_props`)

`inject_sidecar.py::_parse_ext_props(add_meta: List[str]) -> Dict[str, Any]` parses every
`--add` entry into `BisContext.ext_props`. Each entry is one of two forms:

1. **A bare JSON object string** — e.g. `--add '{"AudioCodec": "aac", "AudioSampleRate": 48000}'`.
   Detected by attempting `json.loads(entry)` first; if it parses to a JSON *object*, its
   top-level keys are treated as `META` names and merged directly into the result (a later
   `--add` entry's keys win over an earlier one's on conflict — plain `dict.update()` semantics,
   applied in the order `--add` was repeated). This lets one `--add` supply several properties at
   once, and takes priority over form 2 below even if the JSON content happens to contain a
   literal `=` character.
2. **A `META=VALUE` pair** — e.g. `--add AudioCodec=aac`. Split on the *first* `=`. `META` is
   stripped of surrounding whitespace and must be non-empty. `VALUE` is then itself speculatively
   parsed as JSON (`json.loads(VALUE)`):
   - Parses successfully → the parsed JSON value (dict, list, number, bool, or `null`) is stored.
     This means a numeric-looking `VALUE` like `--add RecordingDuration=3600` is stored as the
     Python `int` `3600`, not the string `"3600"`, with **no need to consult the BIDS field
     table** — the type comes from JSON syntax, not from `META` being a recognized field name.
   - Not valid JSON → `VALUE` is stored verbatim as a plain string (e.g. `--add
     AudioCodec=aac` → `"aac"`, since `aac` alone isn't valid JSON).

**Errors** (raised as `ValueError` by `_parse_ext_props`, caught in `do_main` before any file is
processed — matches [Error Handling](#error-handling)'s "fatal before any file" requirement for
malformed `--add` input):
- An entry with no `=` that also isn't a JSON object → `"expected META=VALUE or a JSON object"`.
- An entry whose `META` (before `=`) is empty/whitespace-only → `"empty META name"`.

**Not yet implemented**: casting `VALUE` to a field's *declared* type from the [BIDS Media-File
Metadata Fields](#bids-media-file-metadata-fields) table (e.g. forcing `AudioChannelCount` to
`integer` and erroring on `--add AudioChannelCount=stereo`). The JSON-based parsing above covers
the common case (numbers/bools/nulls/objects come through typed, plain text stays a string)
without needing that table, but it can't validate/enforce a *specific* field's declared type or
range — see [Open Questions / TODOs](#open-questions--todos).

---

## Algorithm / Data Flow

```
1. [implemented] Parse --add entries into ext_props via _parse_ext_props (JSON-object or
   META=VALUE, VALUE itself JSON-parsed when possible); error out early (before touching any
   file) on a malformed entry, since it applies identically to every file in the batch.

2. [implemented] ctx.videos_tsv is stored from --videos as-is (no upfront index build in
   inject_sidecar.py itself — index construction/caching happens lazily, inside
   get_file_video_audit's own cache, the first time step 3.b.i below looks up a given
   videos_tsv path).

3. For each FILE in FILE1 [FILE2 ...] (_do_sidecar):
   a. [implemented] Validate FILE via parse_bids_media_info(FILE); if not bmi.valid, report the
      BidsMediaInfoError details either way. If --strict: mark this FILE as errored and stop
      processing it. If not --strict (default): report as a warning only and continue to step b —
      not in the original pseudocode below, added as a first-pass sanity check.
   b. [implemented] Extract technical fields:
        i.  [implemented] If ctx.videos_tsv is set: call
            bids_properties_from_video_audit(FILE, ctx.videos_tsv), which looks up FILE in the
            videos.tsv index (via get_file_video_audit(..., cached=True, use_lock=False)) and
            maps the matched VaRecord's columns (plus Device/DeviceSerialNumber from FILE's .log,
            and an inferred VideoCodec) to BIDS fields. If it raises, fall back to step ii for
            this FILE instead.
        ii. [implemented] Otherwise (no --videos, or step i raised): run
            bids_properties_from_ffprobe(FILE) and map AudioInfo/VideoInfo → BIDS fields.
   c. [implemented] Apply --add overrides (ctx.ext_props) on top of extracted fields (highest
      priority) via plain dict.update semantics.
   d. [implemented] Resolve sidecar path: FILE with extension replaced by ".json".
   e. [implemented] Determine existing sidecar content:
        - update mode: load JSON if sidecar exists, else {}; malformed existing JSON → error,
          skip file, no partial merge
        - replace mode: {} (existing content discarded)
   f. [implemented] For each field to be written, apply Conflict Resolution against the existing
      sidecar content (update mode only). On an unresolved conflict (error policy), mark this
      FILE as errored and stop processing it (no partial write).
   g. [implemented] If --dry-run: print the field set that would be written; do not write.
      Else: write merged/replaced JSON to the sidecar path (json.dump(..., indent=2)).

4. [implemented] Report summary: N processed, M written, K errors. Non-zero exit code if K > 0.
```

---

## File / Module Structure

| File                                              | Purpose                                                                 |
|----------------------------------------------------|--------------------------------------------------------------------------|
| `src/reprostim/cli/cmd_bids_inject_sidecar.py`      | Click command definition (`bids-inject-sidecar`)                       |
| `src/reprostim/bids/inject_sidecar.py`              | Core logic: per-file extraction, `--add` parsing, conflict resolution, JSON read/write |
| `src/reprostim/bids/media.py`                       | Shared BIDS media-field taxonomy: `BidsMediaType`/`BidsMediaProperty`/format/codec enums, `BidsMediaInfo`, `parse_bids_media_info` (see [spec-bids-media.md](spec-bids-media.md)) |
| `src/reprostim/bids/properties.py`                  | `AudioInfo`/`VideoInfo`/`VaRecord` → BIDS-dict mapping (`bids_properties_from_ffprobe`, `bids_properties_from_video_audit`), factored out so both `split-video`/`bids-inject` and `bids-inject-sidecar` can share one source of truth (see [spec-bids-properties.md](spec-bids-properties.md)) — both wired into `_do_sidecar` |

> All three modules live under `src/reprostim/bids/`, along with `inject.py` (`bids-inject`'s own
> core logic) — the package reorganization that started with `inject_sidecar.py`/`media.py`
> continued with `inject.py` and now `properties.py`.

Registered in `src/reprostim/cli/entrypoint.py` alongside other commands.

---

## Relationship to `bids-inject` / `split-video`

`split_video.py::_write_sidecar()` (via `bids/properties.py::bids_properties_from_split_result`
for the BIDS-dict mapping itself, moved out of `split_video.py` — see below) is used by
`split-video --sidecar-json` and, transitively, by `bids-inject` (see
[spec-bids-inject.md § Outputs → B](spec-bids-inject.md#b-sidecar-metadata--bep047behavior--reprostim-extras)).
That existing logic is narrower in scope: it only ever writes a **fresh** sidecar for a file
`split-video` itself just produced, with no notion of merging into or reconciling against a
pre-existing sidecar.

`bids-inject-sidecar` is the generalization of that logic to arbitrary existing files, with
explicit merge/conflict semantics. Recommended (but out of scope for the initial
`bids-inject-sidecar` implementation) follow-up work:

1. **Done**: the BIDS field-name/type table lives in `bids/media.py` (`BidsMediaProperty`), and
   the `AudioInfo`/`VideoInfo`/`SplitResult` → BIDS-dict mapping in a separate
   `bids/properties.py` (`bids_properties_from_audio_video_info`/`bids_properties_from_ffprobe`/
   `bids_properties_from_split_result`) — see [spec-bids-properties.md](spec-bids-properties.md).
   `split_video.py::_to_bids_model` was moved into `bids/properties.py` wholesale as
   `bids_properties_from_split_result` (not just referenced from a still-separate
   implementation, as originally proposed) — `split_video.py` has no BIDS-mapping logic of its
   own anymore. `bids/inject.py::_call_split_video` has adopted `bids_properties_from_ffprobe`.
2. **Done**: `PixelFormat`/`BitDepth`/`Width`/`Height` vs `ImagePixelFormat`/`ImageBitDepth`/
   `ImageWidth`/`ImageHeight` reconciled — `bids_properties_from_split_result` writes all four
   `Image*`-prefixed names (see [BIDS Media-File Metadata
   Fields](#bids-media-file-metadata-fields) note above).
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
| Input `FILE` does not exist *(implemented)*                  | Error and skip that file (`_do_sidecar_all`); continue with the rest of the batch. |
| `FILE` fails `parse_bids_media_info` validity check (`bmi.valid is False`), `--strict` set *(implemented)* | Error and skip that file — reported via `_error`, includes the `BidsMediaErrorCode`/message for each `BidsMediaInfoError`. Not in the original spec text; added since `_do_sidecar` calls `parse_bids_media_info` as a first-pass sanity check before extraction. |
| `FILE` fails `parse_bids_media_info` validity check (`bmi.valid is False`), `--strict` not set (default) *(implemented)* | Warning only — reported via `_warn`, includes the same `BidsMediaErrorCode`/message details; file is **not** skipped, processing continues to extraction/write. |
| `ffprobe` not installed / fails                              | Error logged (per existing `get_audio_video_info_ffprobe` behavior); fields it would have supplied are simply omitted, not fatal to the whole file unless no fields at all could be determined and no `--add` compensates. |
| `--videos` given but `FILE` not found in `videos.tsv` *(implemented)* | Not an error — `bids_properties_from_video_audit`/`get_file_video_audit` falls back to auditing the file directly; if that still raises, `_do_sidecar` falls back to `ffprobe` extraction (`_warn`-logged) for that file. |
| Malformed `--add` entry (no `=`, and not a JSON object) *(implemented)* | Fatal `ValueError` from `_parse_ext_props`, caught in `do_main`; applies to whole invocation, before any file is processed. |
| `--add` entry's `META` (before `=`) is empty/whitespace *(implemented)* | Same as above — fatal before any file is processed.                        |
| `--add` value fails declared-type casting for a known BIDS field *(not yet implemented — see [`--add` Value Parsing](#--add-value-parsing-implemented-_parse_ext_props))* | Would be fatal error before any file is processed, once implemented. |
| Existing sidecar JSON is not valid JSON (`update` mode) *(implemented)* | Error and skip that file (`json.JSONDecodeError` caught in `_do_sidecar`); do not attempt a partial merge. |
| Field conflict, `--existing-different error` (default) *(implemented)* | Error and skip that file; report the conflicting field, old and new values (`_error`). |
| Field conflict, `--existing-different overwrite` *(implemented)* | Warn and proceed (`logger.warning` + `_verbose`); value is overwritten.    |
| Sidecar directory not writable *(implemented)*                | Error and skip that file (`OSError` caught around the `open(sidecar_path, "w")` call). |

---

## Open Questions / TODOs

1. **Image file support** — explicitly deferred per issue #259; would need non-audio/video
   decode handling (e.g. Pillow/`ffprobe` for stills), and would use the now-settled
   `ImageWidth`/`ImageHeight`/`ImagePixelFormat`/`ImageBitDepth` naming (see item 4 below).
2. **Format-preserving JSON updates** — evaluate/contribute to
   [bids-utils](https://github.com/bids-standard/bids-utils/) so `update` mode can minimize diffs
   against hand-edited sidecars instead of rewriting with `json.dumps`.
3. **Shared `bids_media.py` extraction** — **done, and taken further than proposed**:
   `_to_bids_model`'s field mapping wasn't just factored out of `split_video.py`, it was *moved*
   wholesale into `bids/properties.py` as `bids_properties_from_split_result` — `split_video.py`
   now imports and calls it rather than containing any mapping logic itself (see
   [Relationship](#relationship-to-bids-inject--split-video)).
4. **Field naming reconciliation** — **resolved**: `bids_properties_from_split_result` (formerly
   `split_video.py::_to_bids_model`) writes all four `Image*`-prefixed BEP044 names —
   `ImageBitDepth`/`ImagePixelFormat` (renamed first, coordinated with
   `bids/inject.py::_call_split_video` switching to `bids_properties_from_ffprobe` — see
   [spec-bids-properties.md](spec-bids-properties.md)), then `ImageWidth`/`ImageHeight` (renamed
   from `SplitResult.video_width`/`video_height`-sourced `Width`/`Height` in a follow-up pass).
   Every key with a matching `BidsMediaProperty` member is written via
   `BidsMediaProperty.*.value`, not a raw string
   literal — see [Relationship](#relationship-to-bids-inject--split-video) item 2.
5. **`--videos` path-matching precision** — `--videos`/`ctx.videos_tsv` is now consulted (see
   Algorithm step 3.b.i above, via `bids_properties_from_video_audit`/`get_file_video_audit`), but
   whether a plain resolved-path match is sufficient, vs. `bids-inject`'s time-range matching
   (`find_video_audit_by_timerange`), hasn't been separately confirmed — still open, see
   [task-bids-inject-sidecar.md](task-bids-inject-sidecar.md).
6. **`--dry-run` / `-v` options** — **implemented and kept**: both work as designed
   (`--dry-run` prints the planned field set without writing; `-v/--verbose` reports per-field
   merge/conflict/write detail via `_verbose`).
7. **Casting failures for unknown-but-numeric-looking `--add` fields** — **resolved differently
   than originally anticipated**: `_parse_ext_props` (implemented) JSON-parses every `VALUE`
   regardless of whether `META` is a known BIDS field, so `--add CustomCount=5` already becomes
   the int `5` — no BIDS-table lookup needed for this case.
8. **Declared-type validation for known BIDS fields** — `_parse_ext_props`'s JSON-based parsing
   does *not* validate against a field's declared type from the [BIDS Media-File Metadata
   Fields](#bids-media-file-metadata-fields) table. E.g. `--add AudioChannelCount=stereo` is
   accepted and stored as the plain string `"stereo"` (not valid JSON, so no error), even though
   `AudioChannelCount` is declared `integer`. Whether/how to add that validation layer on top of
   `ext_props` — and whether it belongs in `_parse_ext_props` itself or a later stage once
   `BidsMediaProperty` carries declared types (see [spec-bids-media.md Open
   Questions](spec-bids-media.md#open-questions--todos)) — is open.
