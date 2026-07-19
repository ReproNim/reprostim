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

---

## Documentation

- [x] `.ai/capture/metadata-spec.md` created
- [x] `.ai/capture/metadata-tasks.md` created (this file)
- [x] `.ai/context.md` — added a `capture/metadata.py` bullet under the `capture/` module list
- [x] `docs/source/api/index.rst` — added `capture.metadata` to the autosummary list

---

## Open Questions / Future Work

- [ ] Typed data classes for parsed metadata (per `type`: `session_begin`/`capture_stop`/
      `session_end`) — see spec's Open Questions. Would let `video/audit.py`, `video/split.py`,
      and `bids/properties.py` stop doing ad-hoc `.get(key)` access on raw dicts.
- [ ] No caching/indexing in `find_metadata_json` — acceptable for current call sites (single
      lookup per video); revisit if that changes.
