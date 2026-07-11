# `bids_media.py` Task List

Tracks implementation progress against [spec-bids-media.md](spec-bids-media.md).

**Status: stub.** The enums (`BidsMediaType`, `AudioFormat`, `VideoFormat`, `ImageFormat`,
`BidsMediaProperty`) are implemented in `src/reprostim/qr/bids_media.py`; the `AudioInfo`/
`VideoInfo` mapping helpers below are still unchecked.

---

## Core Logic

- [x] `BidsMediaType(str, Enum)` — `AUDIO` / `AUDIOVIDEO` / `IMAGE` / `VIDEO` media suffixes per
      BEP044 appendix table
- [x] `AudioFormat(str, Enum)` — `WAV` / `FLAC` / `MP3` / `AAC` / `OGG`, values are bare
      extensions (no leading dot) per BEP044 appendix audio-format table
- [x] `VideoFormat(str, Enum)` — `MP4` / `AVI` / `MKV` / `WEBM`, values are bare extensions per
      BEP044 appendix video-container-format table
- [x] `ImageFormat(str, Enum)` — `JPG` / `PNG` / `SVG` / `WEBP` / `TIF` / `TIFF`, values are bare
      extensions per BEP044 appendix image-format table
- [x] `BidsMediaProperty(str, Enum)` — sidecar JSON property names (value = exact key) with a
      `categories: FrozenSet[BidsMediaType]` attribute per member, sourced from the live BEP044
      Complete Metadata Properties Table; `for_category(category)` classmethod filters by category
- [ ] Add declared value type (`int`/`float`/`str`) per `BidsMediaProperty` member (needed later
      for `--add META=VALUE` casting in `bids-inject-sidecar`)
- [ ] `AudioInfo` -> BIDS-dict mapping helper
- [ ] `VideoInfo` -> BIDS-dict mapping helper
- [ ] Factor `split_video.py::_to_bids_model` to use this module (no behavior change) — note this
      will need to reconcile `_to_bids_model`'s unprefixed `Width`/`Height`/`PixelFormat`/
      `BitDepth` output with `BidsMediaProperty`'s `Image*`-prefixed names first
- [ ] Reconcile `BidsMediaType` with `bids_inject.py::MediaSuffix` (see spec note)

---

## Documentation

- [x] `qr.bids_media` added to RTD API reference autosummary (`docs/source/api/index.rst`)

---

## Tests and Code Coverage

Proposed test file location: `tests/qr/test_bids_media.py`.

- [ ] `BidsMediaType` — all four members present with expected string values
- [ ] `AudioFormat` / `VideoFormat` / `ImageFormat` — all members present with expected
      (dot-less) extension string values
- [ ] `BidsMediaProperty` — all 14 members present with expected string values
- [ ] `BidsMediaProperty` — each member's `.value` equals its exact BIDS sidecar JSON key
- [ ] `BidsMediaProperty.for_category()` — returns the correct property subset for each of
      `AUDIO` / `VIDEO` / `IMAGE` / `AUDIOVIDEO`
- [ ] `BidsMediaProperty` members are directly usable as `dict`/`json.dumps` keys (str equality)
- [ ] Mapping helper: fields absent from `AudioInfo`/`VideoInfo` are omitted from the output
      dict, not `"n/a"`

---

## Open Questions / Future Work

- [ ] Scope / API surface for remaining `AudioInfo`/`VideoInfo` mapping helpers — see spec Open
      Questions
- [ ] Declared value type (`int`/`float`/`str`) per `BidsMediaProperty` member
- [ ] `BidsMediaType` vs. `bids_inject.py::MediaSuffix` reconciliation
- [ ] `BidsMediaProperty`'s `Image*`-prefixed names vs. `split_video.py`/`spec-bids-inject-sidecar.md`'s
      unprefixed `Width`/`Height`/`PixelFormat`/`BitDepth` reconciliation
