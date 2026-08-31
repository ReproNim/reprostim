# `qr-parse` Task List

Tracks implementation progress against [parse-spec.md](parse-spec.md).

---

## CLI Options

- [x] `PATH` argument — path to video file or directory
- [x] `-m / --mode [PARSE|INFO]` — execution mode
- [x] `-g / --grayscale [none|numpy|opencv]` — frame grayscale conversion method; default `cvtcolor`
- [x] `-t / --std-threshold FLOAT` — grayscale std-deviation pre-filter; skip decode when std < threshold; disabled when ≤ 0; default `10.0`
- [x] `-x / --scale FLOAT` — frame downscale factor `(0, 1]`; `1.0` = no resize; default `1.0`
- [x] `-s / --skip INT` — frames to skip after each processed frame; `0` = every frame; default `0`
- [x] `-q / --qr-decoder [none|opencv|pyzbar]` — QR backend; `none` skips decode; default `pyzbar`
- [x] `-v / --video-decoder [opencv]` — video frame backend; only `opencv` supported now; placeholder for `ffmpeg`/`pyav`; default `opencv`
- [x] `-Q / --qrdet` — enable qrdet-based frame pre-filter; default `False`
- [x] `-M / --qrdet-model-size [n|s|m|l]` — qrdet model size; default `s`; only used when `--qrdet` is set
- [x] `-W / --qr-decoder-workers INT` — worker threads for parallel QR decoding; `0`/`1` = sequential (streaming); `N > 1` = parallel (buffered, iframe-ordered)
- [x] `-S / --start-time TEXT` — `auto`/`filename`/ISO 8601; `PARSE` mode only; default `auto`
- [x] `-E / --end-time TEXT` — `auto`/`filename`/ISO 8601; `PARSE` mode only; default `auto`

---

## Core Logic

### PARSE mode
- [x] Read frames via `cv2.VideoCapture`
- [x] Grayscale conversion (`np.mean` — current; candidate for `cv2.cvtColor` optimisation)
- [x] QR detection via `pyzbar.decode`
- [x] Deduplicate consecutive identical QR codes
- [x] Output JSONL (`ParseSummary` + per-code records) to stdout
- [x] Std-deviation pre-filter: compute grayscale std before decode, skip frame if below `--std-threshold`
- [x] Replace `np.mean` grayscale with `cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)` (×10 speedup)
- [x] Replace `np.std` with `cv2.meanStdDev` on grayscale frame (faster, same result)

### Start/end time resolution (`-S` / `-E`)
- [x] `resolve_video_time_info(path_video, start_time_opt, end_time_opt)` — new function in
  `parse.py`, replaces the direct `get_video_time_info` call in `do_parse`
- [x] `auto`/`filename`/explicit-ISO8601 handling for both `-S` and `-E`
- [x] `end_time` resolved before `start_time` (start's `auto` fallback depends on it)
- [x] `end_time` `auto` fallback (no filename match): file mtime (`os.path.getmtime`)
- [x] `start_time` `auto` fallback (no filename match): `end_time - real_duration`, duration via
  `reprostim.video.media_info.get_audio_video_info_ffprobe` (requires `check_ffprobe()`)
- [x] Chronological validation (`start <= end`) only when both are given as explicit ISO 8601
  values via the CLI
- [x] `ParseContext.start_time_opt` / `ParseContext.end_time_opt` fields (default `"auto"`) — the
  option values live on `ctx`, like every other frame-processing setting (`grayscale`, `scale`,
  `qr_decoder`, etc.), rather than as separate `do_parse` parameters; `do_parse` reads
  `ctx.start_time_opt`/`ctx.end_time_opt` directly when calling `resolve_video_time_info`
- [x] `-S/--start-time` / `-E/--end-time` CLI options added to `cmd_qr_parse.py`, threaded through
  `do_main(start_time=..., end_time=...)` → `ParseContext(start_time_opt=..., end_time_opt=...)`
- [x] `do_main`: eager syntax validation (`auto`/`filename`/valid ISO 8601) for `PARSE` mode before
  constructing `ParseContext`, mirroring the existing `scale`/`skip` validation style
- [x] Manually smoke-tested end-to-end against a real non-`ffprobe`-mocked, non-conforming-filename
  video (`ffmpeg`-generated `.mp4`): `auto`/`auto` fallback, `filename`-forced failure, explicit
  ISO 8601 both valid and inverted (validation error), malformed ISO 8601 (clean error, no
  exception) — all behaved as designed
- [x] **Bug found in review, fixed**: an early-return guard added during a manual edit
  (`if not vti.success and (start_time_opt == "filename" or end_time_opt == "filename"): return vti`)
  used `get_video_time_info`'s overall `success` flag (only `True` on a *full* start+end filename
  match) to short-circuit before the per-field `fn_start is None`/`fn_end is None` checks. This
  broke `-S filename` (or `-E filename`) against a partial/start-only ("in-progress recording")
  filename — a case `get_video_time_info` explicitly supports (`pattern1b`/`pattern2b`) — even
  though the requested field (`fn_start`) was available. Removed the guard; the existing per-field
  checks already handle both the working and failing cases correctly. Regression test:
  `test_resolve_start_filename_partial_pattern_succeeds`.
- [x] Automated unit tests for `resolve_video_time_info` — see [Tests](#tests) below

### INFO mode
- [x] Enumerate `.mkv` files in directory (or single file)
- [x] Output `InfoSummary` JSONL (path, duration, size, rate)

---

## Tests

### CLI option handling
- [x] `--grayscale none` — verify raw BGR frame is passed through without conversion
- [x] `--grayscale numpy` — verify `np.mean(frame, axis=2)` path is taken
- [x] `--grayscale opencv` — verify `cv2.cvtColor` path is taken (default)
- [x] `--std-threshold 0` — verify pre-filter is disabled, all frames reach decoder
- [x] `--std-threshold 40` — verify frames below threshold are skipped
- [x] `--scale 0.5` — verify frames are resized before decode
- [x] `--scale 1.0` — verify no resize is applied (default, no-op)
- [x] `--skip 0` — verify every frame is processed
- [x] `--skip 2` — verify only every 3rd frame is processed
- [x] `--qr-decoder none` — verify decode is skipped, output still produced
- [x] `--qr-decoder opencv` — verify `cv2.QRCodeDetector.detectAndDecode` is used
- [x] `--qr-decoder pyzbar` — verify `pyzbar.decode` is used (default)
- [x] `--video-decoder opencv` — verify `cv2.VideoCapture` is used (default)
- [x] `--qrdet` — verify qrdet pre-filter is activated (mocked, no GPU needed)
- [x] `--qrdet-model-size n/s/m/l` — verify correct model variant is loaded (mocked)
- [x] `--qr-decoder-workers 0` — verify sequential path is taken (ThreadPoolExecutor not instantiated)
- [x] `--qr-decoder-workers 1` — verify sequential path is taken (threshold is `> 1`)
- [x] `--qr-decoder-workers 4` — verify ThreadPoolExecutor instantiated with `max_workers=4`
- [x] `--qr-decoder-workers 4` — verify `_process_frame` called once per non-skipped frame
- [x] `--qr-decoder-workers 4` — verify output records match sequential path (data, frame_start, time_start)
- [x] `-S/-E` CLI options forwarded to `do_main` (`test_cli_options_forwarded`,
  `test_cli_start_end_time_default_is_auto`)

### `resolve_video_time_info` (`tests/qr/test_parse.py`)
- [x] `auto`/`auto` with a matching filename — identical to plain `get_video_time_info`
  (`test_resolve_auto_auto_matching_filename`)
- [x] `filename`/`filename` with a matching filename (`test_resolve_filename_filename_matching`)
- [x] `filename`/`filename` on a non-matching filename — fails with a clear error
  (`test_resolve_filename_mode_non_matching_fails`)
- [x] `-S filename` against a partial/start-only-pattern filename — succeeds using the available
  `fn_start` (`test_resolve_start_filename_partial_pattern_succeeds`; the review-bug regression test)
- [x] `-E filename` against the same partial/start-only filename — fails, `fn_end` genuinely
  unavailable (`test_resolve_end_filename_partial_pattern_fails`)
- [x] `auto`/`auto` on a non-matching filename — mtime `end`, `ffprobe`-duration-derived `start`
  (`test_resolve_auto_fallback_non_matching_filename`)
- [x] `auto` start fallback when `ffprobe` isn't installed — clean failure, no exception
  (`test_resolve_auto_fallback_ffprobe_missing`)
- [x] `auto` start fallback when `ffprobe` can't determine duration — clean failure
  (`test_resolve_auto_fallback_ffprobe_duration_unavailable`)
- [x] Both explicit ISO 8601, valid order — used verbatim (`test_resolve_explicit_iso_both_valid`)
- [x] Both explicit ISO 8601, inverted order — validation fails
  (`test_resolve_explicit_iso_both_inverted_fails`)
- [x] Malformed `--start-time` / `--end-time` values — clean failure, no exception
  (`test_resolve_explicit_iso_malformed_start`/`_end`)
- [x] Validation only applies when *both* sides are explicit — an explicit start after a
  filename/auto-derived end is accepted, by design
  (`test_resolve_validation_skipped_when_only_one_side_explicit`)
- [x] Explicit `--start-time` with `--end-time auto` — end still resolves from a matching filename
  (`test_resolve_explicit_start_auto_end_uses_filename`)

### `do_main` (`tests/qr/test_parse.py`)
- [x] Malformed `--start-time` / `--end-time` — returns 1 in `PARSE` mode
  (`test_do_main_invalid_start_time`/`_end_time`)
- [x] `--mode INFO` with malformed `-S`/`-E` — no validation, no effect, returns 0
  (`test_do_main_info_mode_ignores_start_end_time`)
- [x] `start_time`/`end_time` forwarded into `ParseContext`
  (`test_do_main_start_end_time_forwarded_to_parse_context`)

### Integration
- [ ] Combined `--grayscale cvtcolor --std-threshold 40 --skip 1` — verify all three interact correctly on a real video
- [ ] `--qrdet --qr-decoder pyzbar` — verify qrdet pre-filter feeds into pyzbar decode
- [ ] `--qr-decoder none --std-threshold 40` — verify std filter still runs even when decode is disabled
- [ ] QR codes are detected and match expected output on reference test video

### Coverage
- [x] `parse.py` ≥ 80% — achieved **93%**
- [x] `cmd_qr_parse.py` ≥ 80% — achieved **100%**
- [x] `get_video_time_info` edge cases: invalid filename, start-only filename, start ≥ end
- [x] `resolve_video_time_info` — see dedicated subsection above; `parse.py` coverage holds at
  **93%** with the new code fully exercised (remaining gaps are pre-existing, unrelated branches)
- [x] `_decode_qr_pyzbar` / `_decode_qr_opencv` found-code paths
- [x] `_qr_state_machine` — two different QR codes in sequence; QR code at end of video
- [x] `do_parse` — `summary_only=True`; `ignore_errors=True`; `cap.isOpened()=False`
- [x] `do_info` / `do_info_file` — file, directory, invalid path
- [x] `do_main` — path not found, invalid scale, invalid skip, INFO mode, unknown mode, PARSE mode success
- [x] CLI (`cmd_qr_parse`) — basic invocation, `--mode INFO`, option forwarding, invalid path

### Regression
- [x] Existing PARSE mode output unchanged when all new options are at their defaults — full
  existing test suite (`tests/qr/`, `tests/video/`, `tests/bids/`) green after adding `-S/-E`
  plumbing, since `start_time_opt`/`end_time_opt` default to `"auto"` and every existing test
  video's filename matches the pattern (identical resolution path to before)
- [x] Existing INFO mode output unchanged — untouched by this change

---

## Performance / Optimisation (from spec benchmarks)

- [x] `cv2.cvtColor` grayscale (proposal 1) — 23.7 → 46.1 fps
- [x] `cv2.meanStdDev` std deviation (proposal 2)
- [x] Std pre-filter with `--std-threshold` (proposal 3)
- [x] Optional frame downscaling `-x / --scale` (proposal 4)
- [x] Parallel decoding via `ThreadPoolExecutor` + `-W / --qr-decoder-workers` (proposal 5)
- [ ] GPU / ZXing decoder (proposal 6)

---

## Future: Video Decoder Backends

Extend `-v / --video-decoder` with additional backends once `opencv` path is stable.

- [ ] `ffmpeg` — drive frame extraction via `ffmpeg` subprocess or `ffmpeg-python` bindings; useful for formats/codecs OpenCV cannot handle
- [ ] `pyav` — use `av` (PyAV) bindings for libavcodec/libavformat; lower overhead than subprocess, supports hardware-accelerated decode (VAAPI, NVDEC)
- [ ] ? `decord` — GPU-accelerated video reader (`decord` package); designed for ML workloads, supports batch frame reads and CUDA tensors
- [ ] Abstract `_open_video(ctx) -> iterator[frame]` API in `parse.py` so backends are swappable without touching the main frame loop
