# `bids/media.py` Task List

Tracks implementation progress against [spec-bids-media.md](spec-bids-media.md).

**Status: stub.** The enums (`BidsMediaType`, `AudioFormat`, `VideoFormat`, `ImageFormat`,
`BidsMediaProperty`, `BidsMediaCodec`) are implemented in `src/reprostim/bids/media.py`. The
`AudioInfo`/`VideoInfo` mapping helpers moved to a separate module — see
[task-bids-properties.md](task-bids-properties.md) — and are tracked there, not below.

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
- [x] `BidsMediaCodec(str, Enum)` — `H264` / `HEVC` / `VP9` / `AV1` / `AAC` / `MP3` / `OPUS` /
      `FLAC` / `PCM_S16LE`; value = FFmpeg codec name, `rfc6381` attribute = representative RFC
      6381 string (`None` for `PCM_S16LE`), `category: BidsMediaType` (`AUDIO`/`VIDEO`);
      `for_category(category)` classmethod. Non-exhaustive by design — not used for validation.
- [x] `BidsMediaErrorCode(str, Enum)` — `INVALID_PATH` / `UNKNOWN_EXTENSION` /
      `UNKNOWN_MEDIA_TYPE` / `MEDIA_TYPE_MISMATCH`
- [x] `BidsMediaInfoError(BaseModel)` — `code: BidsMediaErrorCode`, `message: str`
- [x] `BidsMediaInfo(BaseModel)` — pure data holder: `path`, `media_type`, `format`
      (`Union[AudioFormat, VideoFormat, ImageFormat]`), `errors: List[BidsMediaInfoError]`,
      computed `valid` property (`not errors`); intentionally has no `from_path`/parsing logic
- [x] `parse_bids_media_info(path: str) -> BidsMediaInfo` — filename-only parsing (no filesystem
      access): resolves `media_type` from the trailing `_<token>` suffix, falls back to guessing
      from the extension (`UNKNOWN_MEDIA_TYPE` error) when the suffix is missing/invalid;
      resolves `format` from the extension independently (`UNKNOWN_EXTENSION` error if
      unrecognized); `INVALID_PATH` error when there's no extension at all
- [ ] `MEDIA_TYPE_MISMATCH` detection (suffix vs. extension inconsistency) — not implemented;
      `parse_bids_media_info` never produces this error code yet
- [x] `AudioInfo`/`VideoInfo` -> BIDS-dict mapping helper — implemented as
      `bids_properties_from_audio_video_info` in `bids/properties.py`, not here; see
      [task-bids-properties.md](task-bids-properties.md)
- [ ] Factor `split_video.py::_to_bids_model` to use `bids/properties.py` (no behavior change) —
      naming is already reconciled (`_to_bids_model` writes `ImageWidth`/`ImageHeight`/
      `ImagePixelFormat`/`ImageBitDepth` via `BidsMediaProperty.*.value`); this item is now just
      about sharing the mapping code, not field names
- [ ] Reconcile `BidsMediaType` with `bids_inject.py::MediaSuffix` (see spec note)

---

## Documentation

- [x] `bids.media` added to RTD API reference autosummary (`docs/source/api/index.rst`)

---

## Tests and Code Coverage

Proposed test file location: `tests/bids/test_media.py`.

- [ ] `BidsMediaType` — all four members present with expected string values
- [ ] `AudioFormat` / `VideoFormat` / `ImageFormat` — all members present with expected
      (dot-less) extension string values
- [ ] `BidsMediaProperty` — all 14 members present with expected string values
- [ ] `BidsMediaProperty` — each member's `.value` equals its exact BIDS sidecar JSON key
- [ ] `BidsMediaProperty.for_category()` — returns the correct property subset for each of
      `AUDIO` / `VIDEO` / `IMAGE` / `AUDIOVIDEO`
- [ ] `BidsMediaProperty` members are directly usable as `dict`/`json.dumps` keys (str equality)
- [ ] `BidsMediaCodec` — all 9 members present with expected FFmpeg-name string values
- [ ] `BidsMediaCodec.rfc6381` — correct for each member, `None` for `PCM_S16LE`
- [ ] `BidsMediaCodec.for_category()` — returns the correct codec subset for `AUDIO` and `VIDEO`
- [ ] Mapping helper: fields absent from `AudioInfo`/`VideoInfo` are omitted from the output
      dict, not `"n/a"`
- [ ] `BidsMediaInfo` — default-constructed with only `path` has `media_type=None`,
      `format=None`, `errors=[]`, `valid=True`
- [ ] `BidsMediaInfo` — `valid` is `False` whenever `errors` is non-empty, and flips back to
      `True` if `errors` is cleared (i.e. it's derived, never stale)
- [ ] `BidsMediaInfo.errors` — supports accumulating more than one `BidsMediaInfoError` (distinct
      `code`s) for a single instance
- [ ] `BidsMediaInfo.format` — accepts a value from any of `AudioFormat`/`VideoFormat`/
      `ImageFormat` (`Union` typing)
- [ ] `BidsMediaInfo` / `BidsMediaInfoError` — round-trip via `model_dump()`/`model_validate()`
- [ ] `parse_bids_media_info` — valid `_video`/`_audio`/`_image`/`_audiovideo` suffix + matching
      extension → correct `media_type`/`format`, no errors
- [ ] `parse_bids_media_info` — suffix token is case-insensitive (e.g. `_VIDEO.MP4`)
- [ ] `parse_bids_media_info` — no valid suffix, recognized audio extension → `media_type=AUDIO`
      guessed from extension, `UNKNOWN_MEDIA_TYPE` error present
- [ ] `parse_bids_media_info` — no valid suffix, recognized image extension → `media_type=IMAGE`
      guessed, `UNKNOWN_MEDIA_TYPE` error present
- [ ] `parse_bids_media_info` — no valid suffix, recognized video-container extension →
      `media_type=VIDEO` guessed (not `AUDIOVIDEO`), `UNKNOWN_MEDIA_TYPE` error present
- [ ] `parse_bids_media_info` — no valid suffix, unrecognized extension → `media_type=None`,
      `format=None`, both `UNKNOWN_MEDIA_TYPE` and `UNKNOWN_EXTENSION` errors present
- [ ] `parse_bids_media_info` — valid suffix, unrecognized extension → `media_type` set from
      suffix, `format=None`, only `UNKNOWN_EXTENSION` error present
- [ ] `parse_bids_media_info` — path with no extension/dot at all → single `INVALID_PATH` error,
      `media_type=None`, `format=None`
- [ ] `parse_bids_media_info` — empty string path → `INVALID_PATH` error
- [ ] `parse_bids_media_info` — accepts a full path (with directories), not just a bare filename

---

## Open Questions / Future Work

- [ ] `AudioInfo`/`VideoInfo` mapping helper follow-ups now tracked in
      [task-bids-properties.md](task-bids-properties.md), not here
- [ ] Declared value type (`int`/`float`/`str`) per `BidsMediaProperty` member
- [ ] `BidsMediaType` vs. `bids_inject.py::MediaSuffix` reconciliation
- [x] `BidsMediaProperty`'s `Image*`-prefixed names vs. `split_video.py`'s output — resolved,
      `_to_bids_model` now writes `ImageWidth`/`ImageHeight`/`ImagePixelFormat`/`ImageBitDepth`
- [ ] `MEDIA_TYPE_MISMATCH` detection — `parse_bids_media_info` never produces it yet; decide
      whether/how (see spec Open Questions)
- [ ] `parse_bids_media_info`'s video-container ambiguity default (`VIDEO` over `AUDIOVIDEO`
      when the suffix can't disambiguate) — confirm acceptable, or prefer `None` instead of a
      guess (see spec Open Questions)
- [ ] `parse_bids_media_info`'s suffix-parsing vs. `bids_inject.py::MediaSuffix` — confirm no
      reuse/extension is warranted (see spec Open Questions)
