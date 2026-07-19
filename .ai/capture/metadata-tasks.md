# Capture Metadata Task List

Tracks implementation progress against [metadata-spec.md](metadata-spec.md).

---

## Module

- [x] `src/reprostim/capture/metadata.py` created
- [x] `JSON_PATTERN`, `iter_metadata_json`, `find_metadata_json` moved here verbatim from
      `video/audit.py` (no behavior change)
- [x] `video/audit.py` — removed the two functions and `JSON_PATTERN`; now imports
      `find_metadata_json` from `reprostim.capture.metadata` (the only one it uses internally, in
      `do_audit_file`); dropped now-unused `import re`
- [x] `video/split.py` — updated to import `find_metadata_json` from `reprostim.capture.metadata`
      instead of `reprostim.video.audit`
- [x] `bids/properties.py` — updated to import `find_metadata_json` from
      `reprostim.capture.metadata` instead of `reprostim.video.audit`; docstring reference to
      `reprostim.video.audit.find_metadata_json` updated to the new path
- [x] `MetadataType(str, Enum)` added — `SESSION_BEGIN`/`CAPTURE_STOP`/`SESSION_END`, mirroring the
      `"type"` values written by `_METADATA_LOG` in
      `src/reprostim-capture/videocapture/src/VideoCapture.cpp` (confirmed exactly these 3 values,
      only 3 call sites, all in that one file)
- [ ] Wire `MetadataType` into the existing `find_metadata_json(..., "type", "session_begin")` call
      sites (`video/audit.py::do_audit_file`, `video/split.py::_split_video`,
      `bids/properties.py::bids_properties_from_video_audit`) — explicitly deferred, not done yet
- [x] `MetadataBase`/`MetadataSessionBegin`/`MetadataCaptureStop`/`MetadataSessionEnd` pydantic
      models added, one per `MetadataType` value, field-for-field from the three `_METADATA_LOG`
      call sites in `VideoCapture.cpp`
- [x] All model fields declared `Optional[str] = None` (per spec, a deliberate weakly-typed first
      pass) — including `cx`/`cy` (JSON numbers) and `autoRecovery` (JSON bool) in
      `MetadataSessionBegin`
- [x] Shared `field_validator("*", mode="before")` on `MetadataBase` stringifies any non-`str`
      input so int/bool JSON values coerce to `str` instead of raising a pydantic validation error
      — verified the wildcard validator is inherited by subclass-only fields too
- [ ] `iter_metadata_json`/`find_metadata_json` still return raw `dict`s — no call site constructs
      these models yet (see spec Open Questions)

---

## Tests

- [x] `tests/capture/test_metadata.py` created — moved `test_iter_metadata_json_*` /
      `test_find_metadata_json_*` here from `tests/video/test_audit.py` (synthetic-log cases:
      valid entry, missing file, invalid JSON, found, not found)
- [x] Added `test_iter_metadata_json_real_sample_log` / `test_find_metadata_json_real_sample_log`
      using the real capture-tool log fixture `tests/data/capture/metadata-videocapture.mkv.log`
      (interleaved ffmpeg output around 3 metadata marker lines: `session_begin`, `capture_stop`,
      `session_end`) — regression coverage against the real log format, not just synthetic lines
- [x] `tests/video/test_audit.py` — removed the moved tests and the now-unused `_write_log` helper
      and `find_metadata_json`/`iter_metadata_json` imports; the existing
      `patch("reprostim.video.audit.find_metadata_json", ...)` in the `do_audit_file` test was left
      as-is (still valid — the name is imported into `video.audit`'s own namespace and called
      unqualified there)
- [x] Full suite green after the move (`tests/capture/`, `tests/video/`, `tests/bids/`)
- [x] `test_metadata_session_begin_from_real_sample_log` / `test_metadata_capture_stop_from_real_sample_log`
      / `test_metadata_session_end_from_real_sample_log` — construct each model from the real
      sample log via `find_metadata_json`, verifying `cx`/`cy`/`autoRecovery` coerce to `str`
- [x] `test_metadata_base_fields_are_optional` — all three models construct with zero args (every
      field defaults to `None`)

---

## Documentation

- [x] `.ai/capture/metadata-spec.md` created
- [x] `.ai/capture/metadata-tasks.md` created (this file)
- [x] `.ai/context.md` — added a `capture/metadata.py` bullet under the `capture/` module list
- [x] `docs/source/api/index.rst` — added `capture.metadata` to the autosummary list

---

## Open Questions / Future Work

- [ ] `Metadata*` models are `str`-only for now (per spec) — no parsed `datetime`/`int`/`bool`
      fields yet.
- [ ] `video/audit.py`, `video/split.py`, `bids/properties.py` still use raw `dict`/`.get(key)`
      results from `find_metadata_json` — none construct `Metadata*` models yet.
- [ ] No caching/indexing in `find_metadata_json` — acceptable for current call sites (single
      lookup per video); revisit if that changes.
- [ ] Existing `find_metadata_json(..., "type", "session_begin")` call sites still pass the raw
      string literal instead of `MetadataType.SESSION_BEGIN` (see above).
