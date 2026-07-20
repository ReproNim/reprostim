# Capture Metadata Task List

Tracks implementation progress against [metadata-spec.md](metadata-spec.md).

---

## Module

- [x] `src/reprostim/capture/metadata.py` created
- [x] `JSON_PATTERN`, `iter_metadata_json`, `find_metadata_json` moved here verbatim from
      `video/audit.py` (no behavior change)
- [x] `video/audit.py` — removed the two functions and `JSON_PATTERN`; dropped now-unused
      `import re`
- [x] `MetadataType(str, Enum)` added — `SESSION_BEGIN`/`CAPTURE_STOP`/`SESSION_END`, mirroring the
      `"type"` values written by `_METADATA_LOG` in
      `src/reprostim-capture/videocapture/src/VideoCapture.cpp` (confirmed exactly these 3 values,
      only 3 call sites, all in that one file)
- [x] `MetadataBase`/`MetadataSessionBegin`/`MetadataCaptureStop`/`MetadataSessionEnd` pydantic
      models added, one per `MetadataType` value, field-for-field from the three `_METADATA_LOG`
      call sites in `VideoCapture.cpp`
- [x] All model fields declared `Optional[str] = None` (per spec, a deliberate weakly-typed first
      pass) — including `cx`/`cy` (JSON numbers) and `autoRecovery` (JSON bool) in
      `MetadataSessionBegin`
- [x] Shared `field_validator("*", mode="before")` on `MetadataBase` stringifies any non-`str`
      input so int/bool JSON values coerce to `str` instead of raising a pydantic validation error
      — verified the wildcard validator is inherited by subclass-only fields too
- [x] `find_metadata_by_class(path, cls) -> Optional[T]` added — finds the first metadata entry
      matching `cls`'s `MetadataType` and constructs `cls(**msg)`
- [x] `_METADATA_TYPE_BY_CLASS` dict + private `_find_metadata_type_by_class(cls)` helper added —
      maps each typed subclass to its `MetadataType`, kept as a standalone lookup table rather than
      a class attribute on the models (deliberate choice — keeps the model classes themselves free
      of anything beyond their raw JSON fields)
- [x] `find_metadata_by_class` returns `None` and logs an error when `cls` has no corresponding
      `MetadataType` (e.g. called with `MetadataBase` itself, or any unregistered subclass) — no
      silent fallback to an untyped/best-effort result
- [x] `video/audit.py::do_audit_file` — switched from
      `find_metadata_json(path + ".log", "type", "session_begin")` + `sb["frameRate"]`/`sb['cx']`/
      `sb['cy']` to `find_metadata_by_class(path + ".log", MetadataSessionBegin)` + typed
      `sb.frameRate`/`sb.cx`/`sb.cy` attribute access
- [x] `video/split.py::_calc_split_data` — switched to `find_metadata_by_class(path + ".log",
      MetadataSessionBegin)` + `sb.vDev or "n/a"`/`sb.serial or "n/a"` (previously
      `sb.get("vDev", "n/a") or "n/a"`/same for `serial`)
- [x] `bids/properties.py::bids_properties_from_video_audit` — same switch as `video/split.py`;
      docstring reference to `find_metadata_json` updated to `find_metadata_by_class`
- [x] `find_metadata_json` no longer imported/called from `video/audit.py`, `video/split.py`, or
      `bids/properties.py` — it's now purely an implementation detail of `find_metadata_by_class`
      within `capture/metadata.py` itself
- [x] `iter_metadata_json`/`find_metadata_json` still return raw `dict`s (unchanged, by design) —
      `find_metadata_by_class` is the only entry point that constructs typed models

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
      and `find_metadata_json`/`iter_metadata_json` imports; `test_do_audit_file_happy_path`'s
      `patch("reprostim.video.audit.find_metadata_json", ...)` updated to
      `find_metadata_by_class`, and its `sb` fixture value changed from a raw dict to a
      `MetadataSessionBegin(...)` instance to match the new attribute-access call site
- [x] `tests/video/test_split.py` — all 5 `@patch("reprostim.video.split.find_metadata_json", ...)`
      decorators on `_calc_split_data` tests updated to `find_metadata_by_class` (all still
      `return_value=None`, so no other change needed)
- [x] `tests/bids/test_properties.py` — `_FIND_METADATA_JSON_PATCH` renamed
      `_FIND_METADATA_BY_CLASS_PATCH` (now patches `find_metadata_by_class`); the 3 tests around
      device/serial recovery updated: dict fixtures → `MetadataSessionBegin(...)` instances, and
      the `assert_called_once_with(...)` call-signature assertion updated from
      `("/data/a.mkv.log", "type", "session_begin")` to `("/data/a.mkv.log", MetadataSessionBegin)`
- [x] Full suite green after the move (`tests/capture/`, `tests/video/`, `tests/bids/`)
- [x] `test_metadata_session_begin_from_real_sample_log` / `test_metadata_capture_stop_from_real_sample_log`
      / `test_metadata_session_end_from_real_sample_log` — construct each model from the real
      sample log via `find_metadata_json`, verifying `cx`/`cy`/`autoRecovery` coerce to `str`
- [x] `test_metadata_base_fields_are_optional` — all three models construct with zero args (every
      field defaults to `None`)
- [x] `test_find_metadata_by_class_session_begin` / `_capture_stop` / `_session_end` — each against
      the real sample log
- [x] `test_find_metadata_by_class_not_found` — no matching entry → `None`
- [x] `test_find_metadata_by_class_unknown_class_logs_error_and_returns_none` — `MetadataBase` (no
      registered `MetadataType`) → `None`, error logged (asserted via `caplog`)

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
- [ ] No caching/indexing in `find_metadata_json`/`find_metadata_by_class` — acceptable for current
      call sites (single lookup per video); revisit if that changes.
