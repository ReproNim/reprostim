# `qr-parse` Task List

Tracks implementation progress against [spec-qr-parse.md](spec-qr-parse.md).

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

### Integration
- [ ] Combined `--grayscale cvtcolor --std-threshold 40 --skip 1` — verify all three interact correctly on a real video
- [ ] `--qrdet --qr-decoder pyzbar` — verify qrdet pre-filter feeds into pyzbar decode
- [ ] `--qr-decoder none --std-threshold 40` — verify std filter still runs even when decode is disabled
- [ ] QR codes are detected and match expected output on reference test video

### Regression
- [ ] Existing PARSE mode output unchanged when all new options are at their defaults
- [ ] Existing INFO mode output unchanged

---

## Performance / Optimisation (from spec benchmarks)

- [x] `cv2.cvtColor` grayscale (proposal 1) — 23.7 → 46.1 fps
- [x] `cv2.meanStdDev` std deviation (proposal 2)
- [x] Std pre-filter with `--std-threshold` (proposal 3)
- [x] Optional frame downscaling `-x / --scale` (proposal 4)
- [ ] Parallel decoding via `ProcessPoolExecutor` (proposal 5)
- [ ] GPU / ZXing decoder (proposal 6)

---

## Future: Video Decoder Backends

Extend `-v / --video-decoder` with additional backends once `opencv` path is stable.

- [ ] `ffmpeg` — drive frame extraction via `ffmpeg` subprocess or `ffmpeg-python` bindings; useful for formats/codecs OpenCV cannot handle
- [ ] `pyav` — use `av` (PyAV) bindings for libavcodec/libavformat; lower overhead than subprocess, supports hardware-accelerated decode (VAAPI, NVDEC)
- [ ] ? `decord` — GPU-accelerated video reader (`decord` package); designed for ML workloads, supports batch frame reads and CUDA tensors
- [ ] Abstract `_open_video(ctx) -> iterator[frame]` API in `qr_parse.py` so backends are swappable without touching the main frame loop
