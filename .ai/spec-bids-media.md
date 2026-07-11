# BIDS Media-File Metadata Helpers Specification

## Overview

`bids_media.py` (`src/reprostim/qr/bids_media.py`) is a proposed shared module providing BIDS
media-file metadata API helpers: the canonical field-name/type table and
`AudioInfo`/`VideoInfo` -> BIDS-dict mapping logic, per the BEP044/media-files proposal
([bids-standard/bids-specification PR
#2367](https://bids-specification--2367.org.readthedocs.build/en/2367/appendices/media-files.html)).

**Status: stub.** Nothing is implemented yet; this document is a placeholder to be fleshed out
once scope is decided.

Relevant to: https://github.com/ReproNim/reprostim/issues/14

---

## Motivation

Both `split_video.py` (`_to_bids_model`) and the proposed `bids-inject-sidecar` command need the
same BIDS media-file field names, types, and `ffprobe`-derived-info mappings. Today that logic
lives inline in `split_video.py`. `bids_media.py` is meant to become the single source of truth
both consumers share, instead of duplicating/drifting field tables.

See [spec-bids-inject-sidecar.md § File / Module
Structure](spec-bids-inject-sidecar.md#file--module-structure) and [§ Relationship to
`bids-inject` / `split-video`](spec-bids-inject-sidecar.md#relationship-to-bids-inject--split-video)
for where this module was first proposed.

---

## Scope

TBD. Expected to cover, at minimum:

- The BIDS media-file field table (name, type, applies-to) from the BEP044 draft.
- Mapping helpers from `video_audit.py`'s `AudioInfo`/`VideoInfo` to BIDS-field dicts.

Out of scope for now: image-file (`_image` suffix) fields — see [BIDS Media-File Metadata
Fields](spec-bids-inject-sidecar.md#bids-media-file-metadata-fields) note on deferred image
support.

---

## Open Questions / TODOs

- [ ] Confirm final scope/API surface (functions vs. constants vs. a small class).
- [ ] Decide field-naming convention (unprefixed `Width`/`Height`/... vs. BEP044's
      `ImageWidth`/`ImageHeight`/... — see [spec-bids-inject-sidecar.md Open Questions
      #4](spec-bids-inject-sidecar.md#open-questions--todos)).
- [ ] Factor `split_video.py::_to_bids_model` to use this module once implemented.
