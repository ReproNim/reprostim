# `bids-inject-sidecar` Task List

Tracks implementation progress against [spec-bids-inject-sidecar.md](spec-bids-inject-sidecar.md).

Most of this list is not implemented yet. A CLI stub exists (`cli/cmd_bids_inject_sidecar.py`),
and `bids/inject_sidecar.py` has the `OverwriteMode`/`ConflictPolicy` enums and `BisContext`
wired (see Core Logic below), but the actual per-file extraction/write logic (`_do_sidecar`) is
still a `TODO`. Unless noted otherwise, items below remain unchecked.

---

## CLI Options

- [ ] `FILE1 [FILE2 ...]` argument — one or more audio/video files, at least one required
- [ ] `-f / --videos PATH` — optional `videos.tsv` for cached-field lookup
- [ ] `-m / --mode [replace|update]` — default `update`
- [ ] `-a / --add META=VALUE` — repeatable, manual field override/addition
- [ ] `-e / --existing-different [error|overwrite]` — default `error`
- [ ] `-v / --verbose`
- [ ] `-d / --dry-run` *(added for consistency with sibling commands; confirm before implementing — see spec Open Questions #6)*

---

## Core Logic

### Enum types / context (implemented)
- [x] `OverwriteMode(str, Enum)` — `REPLACE`/`UPDATE`, backs `--mode`. Defined in
      `bids/inject_sidecar.py`, scoped to this command only — distinct from `bids/inject.py`'s
      own, differently-scoped `OverwriteMode` (same name, different module, different meaning;
      see spec note)
- [x] `ConflictPolicy(str, Enum)` — `ERROR`/`OVERWRITE`, backs `--existing-different`
- [x] `BisContext` carries them as `mode: OverwriteMode` and `conflict_policy: ConflictPolicy`
      fields, defaulting to `UPDATE`/`ERROR`
- [x] `BisContext` also carries `videos_tsv: Optional[str]`, `dry_run: bool`, `verbose: bool`,
      `out_func: Optional[Callable]` — mirrors `bids/inject.py::BiContext`'s field naming/style
- [x] `do_main` converts the CLI's plain `mode`/`existing_different` strings into these enums,
      and passes `videos`/`dry_run`/`verbose`/`out_func` straight through, when constructing
      `BisContext`
- [ ] CLI options (`-m/--mode`, `-e/--existing-different`) still just plain `click.Choice` strings
      passed through to `do_main` — not yet themselves enum-typed at the Click layer (matches the
      `bids/inject.py` convention of converting str → enum only at the core-logic boundary)

### Shared BIDS field mapping (prerequisite refactor)
- [ ] Create `src/reprostim/bids/media.py` with the BIDS Media-File Metadata Fields table (name → type)
- [ ] Factor `AudioInfo`/`VideoInfo` → BIDS-dict mapping out of `split_video.py::_to_bids_model` into `bids_media.py`
- [x] Decided (initial implementation): use unprefixed `Width`/`Height`/`PixelFormat`/`BitDepth` to match current `split_video.py` output (spec Open Questions #4)
- [ ] `split_video.py::_to_bids_model` updated to use the shared mapping (no behavior change to existing `split-video`/`bids-inject` output)
- [ ] *(future, not this issue)* Rename to `ImageWidth`/`ImageHeight`/`ImagePixelFormat`/`ImageBitDepth` per BEP044 — coordinated pass updating spec/task/code/tests for `split-video` (where this mapping is defined) together with this tool

### `--add` parsing and casting
- [ ] Parse `--add META=VALUE` into a dict; error on malformed input (missing `=`)
- [ ] Cast to declared type for known BIDS fields (`int`, `float`, passthrough `str`)
- [ ] Error out (before processing any file) on a casting failure
- [ ] Unknown `META` keys stored verbatim as strings, no casting attempted

### `--videos` cache lookup
- [ ] Load `videos.tsv` once, build path → `VaRecord` index (paths resolved relative to `videos.tsv` location)
- [ ] Match `FILE` against the index by resolved path
- [ ] Map matched `VaRecord` columns (`audio_sr`, `video_res_detected`, codec columns) into BIDS fields
- [ ] Fall back to `ffprobe` extraction for any file not found in the index, or for fields the TSV doesn't carry

### `ffprobe` extraction
- [ ] Reuse `get_audio_video_info_ffprobe` from `src/reprostim/qr/video_audit.py`
- [ ] Map `AudioInfo` fields → BIDS audio fields (`AudioCodec`, `AudioSampleRate`, `AudioChannelCount`, `AudioBitDepth`, `AudioCodecRFC6381`)
- [ ] Map `VideoInfo` fields → BIDS video fields (`VideoCodec`, `VideoFrameRate`, `VideoCodecRFC6381`, `Width`, `Height`, `PixelFormat`, `BitDepth` — unprefixed for now, see Open Questions / Future Work)
- [ ] `RecordingDuration` derived from stream duration
- [ ] Omit (not `"n/a"`) fields that cannot be determined
- [ ] `ffprobe` failure logged, does not abort the whole file unless no fields at all are available

### Sidecar path resolution
- [ ] Derive sidecar path: input file extension replaced with `.json`

### `--mode` write behavior
- [ ] `update` (default) — load existing sidecar if present, merge new fields, preserve untouched existing keys
- [ ] `update` — no existing sidecar → treat as `{}`, write fresh
- [ ] `replace` — discard existing sidecar content entirely, write only this run's fields
- [ ] Malformed existing sidecar JSON (`update` mode) → error, skip file, no partial merge

### Conflict resolution (`--existing-different`)
- [ ] Field absent from existing sidecar → write, no conflict
- [ ] Existing value is `"n/a"` → write new value, no conflict (treated as no prior value)
- [ ] New value equals existing value → no-op, not counted as conflict
- [ ] Existing real value vs. different new real value, `error` (default) → abort file, report field + old/new values
- [ ] Existing real value vs. different new real value, `overwrite` → log warning, write new value
- [ ] Existing real value vs. new value `"n/a"` → `error` is the default outcome regardless of `--existing-different` value; `overwrite` still logs+proceeds
- [ ] `--add`-supplied values subject to identical conflict rules as extracted values (no bypass)

### Dry-run mode
- [ ] `--dry-run` — compute and print per-file field set that would be written, no file writes

### Batch processing / summary
- [ ] Process each `FILE` independently; one file's error does not stop the batch
- [ ] Final summary line: `N processed, M written, K errors`
- [ ] Non-zero exit code when `K > 0`
- [ ] In verbose mode, print per-field extraction/merge/conflict detail

---

## Error Handling

- [ ] Input `FILE` does not exist → error, skip file, continue batch
- [ ] `ffprobe` not installed/fails → logged error, affected fields omitted, file not necessarily fatal
- [ ] `--videos` path not found in `videos.tsv` → fall back to `ffprobe`, not an error
- [ ] Malformed `--add` (missing `=`) → fatal error before any file processed
- [ ] `--add` casting failure for known BIDS field → fatal error before any file processed
- [ ] Sidecar directory not writable → error, skip file

---

## Documentation

- [ ] `bids-inject-sidecar` added to RTD CLI index (`docs/source/cli/`)
- [ ] `bids-inject-sidecar` added to RTD API reference (`docs/source/api/index.rst`)
- [ ] `cmd_bids_inject_sidecar.py` cross-referenced from `.ai/context.md` CLI module list
- [ ] `bids_inject_sidecar.py` / `bids_media.py` cross-referenced from `.ai/context.md` qr module list

---

## Tests and Code Coverage

Proposed test file location: `tests/bids/test_inject_sidecar.py` (mirrors
`tests/qr/test_bids_inject.py` pattern).

### `bids_media.py` (shared mapping)
- [ ] BIDS field table covers all fields listed in spec § BIDS Media-File Metadata Fields
- [ ] `AudioInfo` → BIDS-dict mapping — all fields populated when present
- [ ] `VideoInfo` → BIDS-dict mapping — all fields populated when present
- [ ] Fields absent from `AudioInfo`/`VideoInfo` are omitted from the output dict, not `"n/a"`

### `--add` parsing and casting
- [ ] Valid `META=VALUE` for known integer field → cast to `int`
- [ ] Valid `META=VALUE` for known number field → cast to `float`
- [ ] Valid `META=VALUE` for known string field → used as-is
- [ ] Unknown `META` → stored as string, no casting
- [ ] Malformed input (no `=`) → raises before any file processed
- [ ] Casting failure (e.g. non-numeric value for integer field) → raises before any file processed

### `--videos` cache lookup
- [ ] File found in `videos.tsv` index → cached fields used, `ffprobe` not called for those fields
- [ ] File not found in index → falls back to `ffprobe`
- [ ] No `--videos` given → always uses `ffprobe`

### Conflict resolution
- [ ] Field absent → written without conflict
- [ ] Existing `"n/a"` + new real value → written without conflict
- [ ] Existing == new → no-op, not flagged as conflict
- [ ] Existing real != new real, `error` (default) → file errors, sidecar unchanged
- [ ] Existing real != new real, `overwrite` → warning logged, sidecar updated
- [ ] Existing real value + new `"n/a"`, default `error` → file errors even though mode is default
- [ ] Existing real value + new `"n/a"`, `overwrite` → warning logged, sidecar updated to `"n/a"`
- [ ] Conflict via `--add` value behaves identically to conflict via extracted value

### `--mode`
- [ ] `update` + no existing sidecar → sidecar created with extracted/added fields only
- [ ] `update` + existing sidecar → untouched keys preserved, touched keys merged/conflict-checked
- [ ] `update` + malformed existing JSON → file errors, no partial write
- [ ] `replace` + existing sidecar → existing content discarded entirely
- [ ] `replace` + no existing sidecar → behaves like a fresh write

### Dry-run mode
- [ ] `--dry-run` → no sidecar file written or modified
- [ ] `--dry-run` → per-file planned field set printed

### CLI tests (Click `CliRunner`)
- [ ] `--help` renders without error
- [ ] Missing `FILE` argument → non-zero exit with error message
- [ ] Unknown `--mode` value → Click error (invalid choice)
- [ ] Unknown `--existing-different` value → Click error (invalid choice)
- [ ] Multiple `--add` options accumulate correctly
- [ ] One file erroring in a multi-file batch does not prevent other files from being processed
- [ ] Exit code is non-zero when any file in the batch errors

### Coverage targets

| Module | Target |
|---|---|
| `bids/media.py` | ≥ 90% |
| `bids/inject_sidecar.py` | ≥ 80% |
| `cli/cmd_bids_inject_sidecar.py` | ≥ 80% |

---

## Open Questions / Future Work

- [ ] **Image file support** — `_image` suffix, `Image*` fields already reused from video; needs still-image decode path (issue #259, explicitly deferred)
- [ ] **Format-preserving JSON updates** — evaluate/contribute to [bids-utils](https://github.com/bids-standard/bids-utils/) (issue #259, explicitly deferred)
- [ ] **`bids-inject`/`split-video` delegation** — have `split_video.py::_write_sidecar` optionally call into `bids-inject-sidecar`'s writer once merge semantics are proven
- [ ] **`--videos` matching precision** — confirm plain resolved-path match is sufficient vs. time-range matching
- [ ] **Unknown-field casting** — whether to attempt numeric auto-detection for `--add` fields outside the known BIDS table
