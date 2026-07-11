# `bids_media.py` Task List

Tracks implementation progress against [spec-bids-media.md](spec-bids-media.md).

**Status: stub.** Nothing is implemented yet — `src/reprostim/qr/bids_media.py` currently
contains only a module docstring. All items start unchecked.

---

## Core Logic

- [ ] Define BIDS Media-File Metadata field table (name -> type -> applies-to)
- [ ] `AudioInfo` -> BIDS-dict mapping helper
- [ ] `VideoInfo` -> BIDS-dict mapping helper
- [ ] Factor `split_video.py::_to_bids_model` to use this module (no behavior change)

---

## Tests and Code Coverage

Proposed test file location: `tests/qr/test_bids_media.py`.

- [ ] Field table covers all fields listed in spec-bids-inject-sidecar.md's BIDS Media-File
      Metadata Fields table
- [ ] Fields absent from `AudioInfo`/`VideoInfo` are omitted from the output dict, not `"n/a"`

---

## Open Questions / Future Work

- [ ] Scope / API surface — see spec Open Questions
- [ ] Field naming convention (unprefixed vs. `Image*`-prefixed per BEP044)
