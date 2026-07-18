# `bids-inject-sidecar` Task List

Tracks implementation progress against [inject-sidecar-spec.md](inject-sidecar-spec.md).

**Basic end-to-end logic is implemented, with automated tests at 100% statement/branch coverage**
of both `bids/inject_sidecar.py` and `cli/cmd_bids_inject_sidecar.py`
(`tests/bids/test_inject_sidecar.py`, 78 tests): `ffprobe`-only extraction, `--videos`/`videos.tsv`
cache lookup (via `bids_properties_from_video_audit`, falling back to `ffprobe`), `--add` merge,
`update`/`replace` modes, `error`/`overwrite` conflict resolution, `--strict`/non-strict
`bmi.valid` handling, `--dry-run`, the `N processed, M written, K errors` summary, and the full
Click CLI options layer (via `CliRunner`) all covered. **Not implemented**: `--add` declared-type
casting.

**Bug fixed while adding CLI tests:** `bids_inject_sidecar`'s `return res` never actually set the
process exit code — Click discards a plain callback return value in standalone mode (see
`click/core.py::BaseCommand.main`'s explicit comment "it's not safe to `ctx.exit(rv)` here" — it
always calls `ctx.exit()` with no args after `invoke()` returns). Confirmed via a real subprocess
run: `bids-inject-sidecar --strict <bad-file>` reported `1 errors` in its own summary line but
exited `0`. Fixed to `if res: ctx.exit(res)`, matching the convention already used in
`cmd_video_audit.py`. `cmd_split_video.py` has the identical `return res` pattern and is likely
affected too, but that's out of scope here — not touched.

---

## CLI Options

All defined in `cli/cmd_bids_inject_sidecar.py`; `-f/--videos` is consulted by `_do_sidecar`
(see `--videos` cache lookup section below).

- [x] `FILE1 [FILE2 ...]` argument — one or more audio/video files, at least one required
- [x] `-f / --videos PATH` — optional `videos.tsv` for cached-field lookup
- [x] `-m / --mode [replace|update]` — default `update`
- [x] `-a / --add META=VALUE` — repeatable, manual field override/addition
- [x] `-e / --existing-different [error|overwrite]` — default `error`
- [x] `-s / --strict` — boolean flag, default `False`. When set, a file failing the `bmi.valid`
      check (`parse_bids_media_info`) is a fatal error for that file (logged at error level,
      reported via `out_func` with an `"Error: "` prefix, file skipped). When not set (default),
      the same problem is only reported as a warning (`out_func` with a `"Warn: "` prefix) and
      processing continues through to extraction/write for that file.
- [x] `-v / --verbose`
- [x] `-d / --dry-run` — kept, see spec Open Questions #6 (now resolved: implemented and kept)

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
- [x] `BisContext` also carries `videos_tsv: Optional[str]`, `strict: bool` (default `False`),
      `dry_run: bool`, `verbose: bool`, `out_func: Optional[Callable]` — mirrors
      `bids/inject.py::BiContext`'s field naming/style
- [x] `BisContext.ext_props: Dict[str, Any]` — parsed `--add` result, see `--add` parsing section
      below
- [x] `do_main` converts the CLI's plain `mode`/`existing_different` strings into these enums,
      parses `add_meta` via `_parse_ext_props` (fatal-before-processing on error), and passes
      `videos`/`dry_run`/`verbose`/`out_func`/`ext_props` straight through, when constructing
      `BisContext`
- [ ] CLI options (`-m/--mode`, `-e/--existing-different`) still just plain `click.Choice` strings
      passed through to `do_main` — not yet themselves enum-typed at the Click layer (matches the
      `bids/inject.py` convention of converting str → enum only at the core-logic boundary)

### Shared BIDS field mapping (prerequisite refactor)
- [x] Create `src/reprostim/bids/media.py` with the BIDS Media-File Metadata Fields table (name → type)
- [x] Factor `AudioInfo`/`VideoInfo` → BIDS-dict mapping out — done as a separate module,
      `bids/properties.py` (`bids_properties_from_audio_video_info`), not inside `bids/media.py`
      itself; see [properties-tasks.md](properties-tasks.md)
- [x] **Superseded**: field names are `Image*`-prefixed BEP044 names throughout, not the
      unprefixed `Width`/`Height`/`PixelFormat`/`BitDepth` this item originally decided on as an
      interim measure — see next item.
- [x] `split_video.py::_to_bids_model` updated to use the shared `bids/properties.py` mapping
      code — **done by moving it there wholesale**, as `bids_properties_from_split_result`;
      `split_video.py` no longer has any BIDS-mapping logic of its own (see
      [properties-tasks.md](properties-tasks.md))
- [x] Renamed to `ImageWidth`/`ImageHeight`/`ImagePixelFormat`/`ImageBitDepth` per BEP044 —
      done in `bids_properties_from_split_result` (formerly `split_video.py::_to_bids_model`),
      coordinated with `bids/inject.py::_call_split_video` adopting `bids_properties_from_ffprobe`;
      not yet propagated to `bids-inject-sidecar` itself since `_do_sidecar` isn't implemented yet

### `--add` parsing (implemented: `_parse_ext_props`)
- [x] Parse `--add META=VALUE` into a dict; error (`ValueError`) on malformed input (no `=` and
      not a JSON object)
- [x] Error (`ValueError`) on an empty/whitespace-only `META` name
- [x] Bare JSON object `--add` entry (e.g. `--add '{"AudioCodec": "aac"}'`) merges its top-level
      keys directly into the result, taking priority over `META=VALUE` splitting
- [x] `VALUE` speculatively JSON-parsed — numbers/bools/`null`/objects/arrays come through typed;
      falls back to a plain string when not valid JSON
- [x] Multiple `--add` entries merge in order, later keys win on conflict (`dict.update()`)
- [x] `do_main` catches `_parse_ext_props`'s `ValueError`, reports via `out_func`/`logger.error`,
      returns `1` before any file is processed
- [x] `BisContext.ext_props: Dict[str, Any]` holds the parsed result, populated in `do_main`
- [ ] Cast to declared type for known BIDS fields (`int`, `float`, passthrough `str`) — **not
      implemented**; JSON-based parsing above already handles the common numeric/bool/null case
      without a field-type table, but does not validate/enforce a *specific* known field's
      declared type (see spec Open Questions #8)

### `--videos` cache lookup (implemented)
- [x] Load `videos.tsv` once, build path → `VaRecord` index (paths resolved relative to
      `videos.tsv` location) — via `get_file_video_audit(path, path_tsv, cached=True,
      use_lock=False)` in `bids_properties_from_video_audit`
- [x] Match `FILE` against the index by resolved path
- [x] Map matched `VaRecord` columns (`duration`, `video_res_recorded`, `video_fps_recorded`,
      `audio_sr`) into BIDS fields — plus `Device`/`DeviceSerialNumber` recovered from
      `<path>.log`'s `session_begin` metadata, and `VideoCodec` inferred as `"h264"`; see
      `bids_properties_from_video_audit`'s docstring for the full mapping
- [x] Fall back to `ffprobe` extraction for any file not found in the index, or for fields the TSV
      doesn't carry — `bids_properties_from_video_audit` itself falls back to auditing the file
      directly when there's no matching row; `_do_sidecar` additionally falls back to
      `bids_properties_from_ffprobe` if `bids_properties_from_video_audit` raises

### `ffprobe` extraction (implemented)
- [x] Reuse `bids/properties.py::bids_properties_from_ffprobe` — `_do_sidecar` calls it directly
      (`props: dict = bids_properties_from_ffprobe(path)`), not reimplemented
- [x] `AudioInfo`/`VideoInfo` → BIDS field mapping — inherited for free from
      `bids_properties_from_ffprobe`/`bids_properties_from_audio_video_info`; see
      [properties-tasks.md](properties-tasks.md) for that mapping's own checklist
- [x] `RecordingDuration` derived from stream duration — same, inherited
- [x] Omit (not `"n/a"`) fields that cannot be determined — same, inherited (`_set_prop` skips
      `None` values)
- [x] `ffprobe` failure logged, does not abort the whole file unless no fields at all are
      available — same, inherited (`get_audio_video_info_ffprobe` catches its own subprocess
      failures and returns empty `AudioInfo`/`VideoInfo` rather than raising)
- [x] `bmi.valid` check (`parse_bids_media_info`) — **not in the original checklist**, added as
      a first-pass sanity check before extraction; reports the `BidsMediaInfoError` detail either
      way. In `--strict` mode (`ctx.strict=True`) an invalid file is a fatal error and is skipped
      (via `_error`); by default (`ctx.strict=False`) it's only reported as a warning (via
      `_warn`) and processing continues to extraction/write for that file (see spec Error
      Handling table)

### Sidecar path resolution (implemented)
- [x] Derive sidecar path: input file extension replaced with `.json`
      (`os.path.splitext(path)[0] + ".json"`)

### `--mode` write behavior (implemented)
- [x] `update` (default) — load existing sidecar if present, merge new fields, preserve untouched existing keys
- [x] `update` — no existing sidecar → treat as `{}`, write fresh
- [x] `replace` — discard existing sidecar content entirely, write only this run's fields
- [x] Malformed existing sidecar JSON (`update` mode) → error, skip file, no partial merge
      (`json.JSONDecodeError` caught)

### Conflict resolution (`--existing-different`) (implemented)
- [x] Field absent from existing sidecar → write, no conflict
- [x] Existing value is `"n/a"` → write new value, no conflict (treated as no prior value)
- [x] New value equals existing value → no-op, not counted as conflict
- [x] Existing real value vs. different new real value, `error` (default) → abort file, report field + old/new values
- [x] Existing real value vs. different new real value, `overwrite` → log warning, write new value
- [x] Existing real value vs. new value `"n/a"` → falls into the same policy-driven "differs"
      branch as the row above — no special case needed, matches spec exactly
- [x] `--add`-supplied values subject to identical conflict rules as extracted values (no
      bypass) — `fields = dict(props); fields.update(ctx.ext_props)` merges both into one dict
      before the conflict-resolution loop runs, so there's no way to distinguish origin at that
      point

### Dry-run mode (implemented)
- [x] `--dry-run` — compute and print per-file field set that would be written, no file writes

### Batch processing / summary (implemented)
- [x] Process each `FILE` independently; one file's error does not stop the batch
- [x] Final summary line: `N processed, M written, K errors` (`[DRY-RUN] ` prefix when `--dry-run`)
- [x] Non-zero exit code when `K > 0`
- [x] In verbose mode, print per-field extraction/merge/conflict detail — via `_verbose(ctx, msg)`
      (new shared helper, mirrors `_error`; logs at debug level always, echoes to `out_func` only
      when `ctx.verbose`)

---

## Error Handling

- [x] Input `FILE` does not exist → error, skip file, continue batch
- [x] `FILE` fails `bmi.valid` check, `--strict` set → error (reports `BidsMediaInfoError`
      details), skip file, continue batch — not in the original checklist, added
- [x] `FILE` fails `bmi.valid` check, `--strict` not set (default) → info-level log only (reports
      `BidsMediaInfoError` details), file still processed — not in the original checklist, added
- [x] `ffprobe` not installed/fails → logged error, affected fields omitted, file not necessarily fatal
- [x] `--videos` path not found in `videos.tsv` → fall back to `ffprobe`, not an error
- [x] Malformed `--add` (missing `=`) → fatal error before any file processed
- [ ] `--add` casting failure for known BIDS field → fatal error before any file processed — N/A,
      declared-type casting isn't implemented (see spec Open Questions #8)
- [x] Sidecar directory not writable → error, skip file (`OSError` around the write)

---

## Documentation

- [x] `bids-inject-sidecar` added to RTD CLI index (`docs/source/cli/bids-inject-sidecar.rst`,
      referenced from `docs/source/cli/index.rst`)
- [x] `bids-inject-sidecar` added to RTD API reference (`docs/source/api/index.rst` →
      `bids.inject_sidecar`)
- [x] `cmd_bids_inject_sidecar.py` cross-referenced from `.ai/context.md` CLI module list
- [x] `inject_sidecar.py` / `media.py` cross-referenced from `.ai/context.md` `bids/` module list
      *(module moved from `qr/` to `bids/` since this item was written)*

---

## Tests and Code Coverage

Test file: `tests/bids/test_inject_sidecar.py` — **78 tests total** (52 core-logic tests + 26 CLI
tests, see below), **100% statement/branch coverage of both `bids/inject_sidecar.py` and
`cli/cmd_bids_inject_sidecar.py`**
(`pytest --cov=reprostim.bids.inject_sidecar --cov=reprostim.cli.cmd_bids_inject_sidecar --cov-report=term-missing`).
Uses real filenames with valid/invalid BIDS suffixes for `parse_bids_media_info` (no mocking
needed — it's pure path parsing) and real `tmp_path` files for sidecar read/write; only
`bids_properties_from_ffprobe` is mocked (patched at
`reprostim.bids.inject_sidecar.bids_properties_from_ffprobe`), matching the codebase convention
of never invoking real `ffprobe`/`subprocess` in unit tests.

*(`bids/media.py`'s own test checklist — field table, `AudioInfo`/`VideoInfo` mapping — is
tracked in [media-tasks.md](media-tasks.md)/[properties-tasks.md](properties-tasks.md),
not here; this file previously had a duplicate/misplaced copy of that checklist, removed.)*

### `OverwriteMode` / `ConflictPolicy` / `BisContext` (implemented)
- [x] `OverwriteMode`/`ConflictPolicy` member values
- [x] `BisContext` defaults
- [x] `BisContext` with all fields explicitly set

### `--add` parsing (`_parse_ext_props`) (implemented)
- [x] `META=VALUE` with a JSON-parseable `VALUE` (e.g. `RecordingDuration=3600`) → int/float/bool/
      null/dict/list per JSON, not a string
- [x] `META=VALUE` with a non-JSON `VALUE` (e.g. `AudioCodec=aac`) → stored as a plain string
- [x] Bare JSON object entry (e.g. `'{"AudioCodec": "aac", "AudioSampleRate": 48000}'`) → all
      top-level keys merged into the result
- [x] Bare JSON object entry takes priority even when its content contains a literal `=`
- [x] Multiple entries with a conflicting key (via plain `META=VALUE`, bulk JSON, or both) → last
      one wins
- [x] Malformed input (no `=`, not a JSON object) → raises `ValueError` before any file processed
- [x] Empty/whitespace-only `META` (e.g. `'=novalue'`) → raises `ValueError`
- [x] Empty `add_meta` list → `{}`
- [x] `do_main` with a malformed `--add` → returns `1`, reports via `out_func`, no file touched
      (both with and without `out_func`)

### `_error` / `_verbose` / `_warn` (implemented)
- [x] `_error` — logs and reports via `out_func` with `"Error: "` prefix; no-`out_func` doesn't raise
- [x] `_verbose` — reports via `out_func` only when `ctx.verbose`; no-`out_func` doesn't raise
- [x] `_warn` — logs at info level and reports via `out_func` with `"Warn: "` prefix regardless of
      `ctx.verbose` (unlike `_verbose`); no-`out_func` doesn't raise; returns `None`

### `--strict` / non-strict `bmi.valid` handling (implemented)
- [x] `--strict` set, invalid `bmi` → `_error` called (`"Error: "` prefix), `_do_sidecar` returns
      `False`, `ffprobe` never invoked
- [x] `--strict` not set (default), invalid `bmi` → `_warn` called (`"Warn: "` prefix),
      `_do_sidecar` continues on to extraction/write and returns `True` on success
- [x] Same distinction exercised at `_do_sidecar_all` and `do_main` level (batch error counts /
      exit codes reflect strict vs. non-strict)

### `--videos` cache lookup (implemented)
- [x] File found in `videos.tsv` index → cached fields used, `ffprobe` not called
      (`test_do_sidecar_videos_tsv_uses_video_audit_not_ffprobe`)
- [x] `bids_properties_from_video_audit` raises → falls back to `ffprobe`
      (`test_do_sidecar_videos_tsv_failure_falls_back_to_ffprobe`) — file-not-found-in-index
      itself is handled inside `bids_properties_from_video_audit`/`get_file_video_audit` (falls
      back to auditing directly), not exercised as a separate `_do_sidecar`-level case here
- [x] No `--videos` given → always uses `ffprobe`, `bids_properties_from_video_audit` never called
      (`test_do_sidecar_no_videos_tsv_uses_ffprobe_only`)

### Conflict resolution (implemented)
- [x] Field absent → written without conflict
- [x] Existing `"n/a"` + new real value → written without conflict
- [x] Existing == new → no-op, not flagged as conflict
- [x] Existing real != new real, `error` (default) → file errors, sidecar unchanged
- [x] Existing real != new real, `overwrite` → warning logged, sidecar updated
- [x] Existing real value + new `"n/a"`, default `error` → file errors even though mode is default
- [ ] Existing real value + new `"n/a"`, `overwrite` → warning logged, sidecar updated to `"n/a"`
      *(not directly tested — the `error`-policy variant is, and the code path is identical/shared
      with the general "differs" branch already covered by the `overwrite`-policy test)*
- [x] Conflict via `--add` value behaves identically to conflict via extracted value — implicit:
      `_do_sidecar` merges `ext_props` into `fields` before the conflict loop runs, so there's no
      code-level distinction to test separately (see `test_do_sidecar_ext_props_override_extracted_fields`)

### `--mode` (implemented)
- [x] `update` + no existing sidecar → sidecar created with extracted/added fields only
- [x] `update` + existing sidecar → untouched keys preserved, touched keys merged/conflict-checked
- [x] `update` + malformed existing JSON → file errors, no partial write
- [x] `replace` + existing sidecar → existing content discarded entirely
- [x] `replace` + malformed existing JSON → not even read, no error (replace mode never loads
      existing content) — extra case beyond the original checklist
- [ ] `replace` + no existing sidecar → behaves like a fresh write *(not separately tested — same
      code path as "existing sidecar discarded", just with no file to discard)*

### Dry-run mode (implemented)
- [x] `--dry-run` → no sidecar file written or modified
- [x] `--dry-run` → per-file planned field set printed (`_do_sidecar` and `do_main` both)
- [x] `--dry-run` with no `out_func` doesn't raise

### `_do_sidecar_all` / `do_main` batch behavior (implemented)
- [x] Invalid path (doesn't exist on disk) counted as an error, distinct from an existing file
      that itself fails (`bmi.valid` or write failure)
- [x] Zero errors when every file succeeds
- [x] Summary line format (`N processed, M written, K errors`), including `[DRY-RUN] ` prefix
- [x] Non-zero exit code when any file errors; zero when all succeed
- [x] `--add` values flow all the way through to the written sidecar

### CLI tests (Click `CliRunner`) (implemented)

Same file, `tests/bids/test_inject_sidecar.py`, appended `# CLI tests (Click CliRunner) for
cmd_bids_inject_sidecar` section (26 tests; `bids_inject_sidecar` imported directly from
`reprostim.cli.cmd_bids_inject_sidecar`, not a separate `tests/cli/` module). Most tests mock
`do_main` at `reprostim.bids.inject_sidecar.do_main` (the point of use — `bids_inject_sidecar`
does `from ..bids.inject_sidecar import do_main` inside the function body) and assert on
`mock.call_args.kwargs`, matching the `tests/qr/test_split_video.py` CLI-test convention; three
"end-to-end" tests instead mock only `bids_properties_from_ffprobe` and let the real `do_main`
run, to exercise the batch/exit-code behavior below through the actual Click layer.

- [x] `--help` renders without error
- [x] Missing `FILE` argument → non-zero exit with error message
- [x] `FILE` argument that doesn't exist on disk → non-zero exit (`click.Path(exists=True)`)
- [x] Unknown `--mode` value → Click error (invalid choice)
- [x] Unknown `--existing-different` value → Click error (invalid choice)
- [x] `--videos` path that doesn't exist on disk → non-zero exit (`click.Path(exists=True)`)
- [x] Multiple `--add` options accumulate correctly (passed through as an ordered list)
- [x] Multiple `FILE` arguments passed through as a list
- [x] `--mode`/`--existing-different`/`--strict`/`--dry-run`/`--verbose`/`--videos` each have
      their default and explicit-value cases verified against `do_main`'s kwargs
- [x] `out_func` passed to `do_main` is `click.echo`
- [x] `-v/--verbose` prints the "completed in ... sec" summary line; without it, the line is absent
- [x] One file erroring in a multi-file batch does not prevent other files from being processed
      (end-to-end: a `--strict`-invalid file alongside a valid one — the valid file's sidecar is
      still written)
- [x] Exit code is non-zero when any file in the batch errors (end-to-end, real `do_main`) — this
      required the `ctx.exit(res)` bug fix above; before that fix this assertion would have failed
- [x] Exit code is zero on a fully successful run (end-to-end, real `do_main`)

### Coverage targets

| Module | Target | Actual |
|---|---|---|
| `bids/media.py` | ≥ 90% | **100%** (see media-tasks.md) |
| `bids/inject_sidecar.py` | ≥ 80% | **100%** (statement + branch) |
| `cli/cmd_bids_inject_sidecar.py` | ≥ 80% | **100%** (statement + branch) |

---

## Open Questions / Future Work

- [ ] **Image file support** — `_image` suffix, `Image*` fields already reused from video; needs still-image decode path (issue #259, explicitly deferred)
- [ ] **Format-preserving JSON updates** — evaluate/contribute to [bids-utils](https://github.com/bids-standard/bids-utils/) (issue #259, explicitly deferred)
- [ ] **`bids-inject`/`split-video` delegation** — have `split_video.py::_write_sidecar` optionally call into `bids-inject-sidecar`'s writer once merge semantics are proven
- [ ] **`--videos` matching precision** — confirm plain resolved-path match is sufficient vs. time-range matching
- [ ] **Unknown-field casting** — whether to attempt numeric auto-detection for `--add` fields outside the known BIDS table
