# `qr-parse` Task List

Tracks implementation progress against [spec-qr-parse.md](spec-qr-parse.md).

---

## CLI Options

- [x] `PATH` argument — path to video file or directory
- [x] `-m / --mode [PARSE|INFO]` — execution mode
- [x] `-g / --grayscale [none|numpy|opencv]` — frame grayscale conversion method; default `cvtcolor`
- [ ] `-t / --std-threshold FLOAT` — grayscale std-deviation pre-filter; skip decode when std < threshold; disabled when ≤ 0; default `10.0`
- [x] `-x / --scale FLOAT` — frame downscale factor `(0, 1]`; `1.0` = no resize; default `1.0`
- [ ] `-s / --skip INT` — frames to skip after each processed frame; `0` = every frame; default `0`
- [ ] `-q / --qr-decoder [none|opencv|pyzbar]` — QR backend; `none` skips decode; default `pyzbar`
- [ ] `-v / --video-decoder [opencv]` — video frame backend; only `opencv` supported now; placeholder for `ffmpeg`/`pyav`; default `opencv`
- [ ] `-Q / --qrdet` — enable qrdet-based frame pre-filter; default `False`
- [ ] `-M / --qrdet-model-size [n|s|m|l]` — qrdet model size; default `s`; only used when `--qrdet` is set

---

## Core Logic

### PARSE mode
- [x] Read frames via `cv2.VideoCapture`
- [x] Grayscale conversion (`np.mean` — current; candidate for `cv2.cvtColor` optimisation)
- [x] QR detection via `pyzbar.decode`
- [x] Deduplicate consecutive identical QR codes
- [x] Output JSONL (`ParseSummary` + per-code records) to stdout
- [ ] Std-deviation pre-filter: compute grayscale std before decode, skip frame if below `--std-threshold`
- [x] Replace `np.mean` grayscale with `cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)` (×10 speedup)
- [ ] Replace `np.std` with `cv2.meanStdDev` on grayscale frame (faster, same result)

### INFO mode
- [x] Enumerate `.mkv` files in directory (or single file)
- [x] Output `InfoSummary` JSONL (path, duration, size, rate)

---

## Tests

### CLI option handling
- [ ] `--grayscale none` — verify raw BGR frame is passed through without conversion
- [ ] `--grayscale mean` — verify `np.mean(frame, axis=2)` path is taken
- [ ] `--grayscale cvtcolor` — verify `cv2.cvtColor` path is taken (default)
- [ ] `--std-threshold 0` — verify pre-filter is disabled, all frames reach decoder
- [ ] `--std-threshold 40` — verify frames below threshold are skipped
- [ ] `--scale 0.5` — verify frames are resized before decode
- [ ] `--scale 1.0` — verify no resize is applied (default, no-op)
- [ ] `--skip 0` — verify every frame is processed
- [ ] `--skip 2` — verify only every 3rd frame is processed
- [ ] `--qr-decoder none` — verify decode is skipped, output still produced
- [ ] `--qr-decoder opencv` — verify `cv2.QRCodeDetector.detectAndDecode` is used
- [ ] `--qr-decoder pyzbar` — verify `pyzbar.decode` is used (default)
- [ ] `--video-decoder opencv` — verify `cv2.VideoCapture` is used (default)
- [ ] `--qrdet` — verify qrdet pre-filter is activated
- [ ] `--qrdet-model-size n/s/m/l` — verify correct model variant is loaded

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

- [ ] `cv2.cvtColor` grayscale (proposal 1) — 23.7 → 46.1 fps
- [ ] `cv2.meanStdDev` std deviation (proposal 2)
- [ ] Std pre-filter with `--std-threshold` (proposal 3)
- [x] Optional frame downscaling `-x / --scale` (proposal 4)
- [ ] Parallel decoding via `ProcessPoolExecutor` (proposal 5)
- [ ] GPU / ZXing decoder (proposal 6)
