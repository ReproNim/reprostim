# `bids_media.py` Task List

Tracks implementation progress against [spec-bids-media.md](spec-bids-media.md).

**Status: stub.** Only `BidsMediaType` is implemented in `src/reprostim/qr/bids_media.py` so far;
the field table and mapping helpers below are still unchecked.

---

## Core Logic

- [x] `BidsMediaType(str, Enum)` — `AUDIO` / `AUDIOVIDEO` / `IMAGE` / `VIDEO` media suffixes per
      BEP044 appendix table
- [ ] Define BIDS Media-File Metadata field table (name -> type -> applies-to)
- [ ] `AudioInfo` -> BIDS-dict mapping helper
- [ ] `VideoInfo` -> BIDS-dict mapping helper
- [ ] Factor `split_video.py::_to_bids_model` to use this module (no behavior change)
- [ ] Reconcile `BidsMediaType` with `bids_inject.py::MediaSuffix` (see spec note)

---

## Documentation

- [x] `qr.bids_media` added to RTD API reference autosummary (`docs/source/api/index.rst`)

---

## Tests and Code Coverage

Proposed test file location: `tests/qr/test_bids_media.py`.

- [ ] `BidsMediaType` — all four members present with expected string values
- [ ] Field table covers all fields listed in spec-bids-inject-sidecar.md's BIDS Media-File
      Metadata Fields table
- [ ] Fields absent from `AudioInfo`/`VideoInfo` are omitted from the output dict, not `"n/a"`

---

## Open Questions / Future Work

- [ ] Scope / API surface for remaining field-table/mapping helpers — see spec Open Questions
- [ ] Field naming convention (unprefixed vs. `Image*`-prefixed per BEP044)
- [ ] `BidsMediaType` vs. `bids_inject.py::MediaSuffix` reconciliation
