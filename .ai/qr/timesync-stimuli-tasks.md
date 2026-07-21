# `timesync-stimuli` Task List

Tracks implementation progress for unit tests, CI/CD virtual audio support,
and audio/video recording artifacts for `timesync-stimuli`.

---

## Unit Tests

Test file location: `tests/qr/test_timesync_stimuli.py`.

### Module-level constants and enums

- [ ] `Mode` enum — values `EVENT`, `INTERVAL`, `BEEP`, `DEVICES` exist and are string-valued
- [ ] `MAX_TR_TIMEOUT` — equals `4.0`

### `SeriesData` dataclass

- [ ] `SeriesData(num=1)` — `tr_count` defaults to `0`, `tr_last_time` to `None`, `tr_timeout` to `MAX_TR_TIMEOUT`
- [ ] `SeriesData` fields can be updated after construction

### `get_ts_str`

- [ ] Known `datetime` → correct `YYYY.MM.DD-HH.MM.SS.mmm` string (millisecond precision, not microseconds)
- [ ] Midnight `datetime(2025, 1, 1, 0, 0, 0)` → `"2025.01.01-00.00.00.000"`
- [ ] Microseconds are truncated to milliseconds (last 3 digits of `%f` dropped)

### `get_output_file_name`

- [ ] Prefix + start only → filename ends with `"--{}.log"` pattern (no end timestamp)
- [ ] Prefix + start + end → filename contains both timestamps separated by `"--"`
- [ ] Output is `"{prefix}{start_str}--{end_str}.log"` for two timestamps
- [ ] Output is `"{prefix}{start_str}--.log"` when `end_ts=None`

### `safe_remove`

- [ ] Existing file → file deleted, no exception raised
- [ ] Non-existing file → no exception, warning logged
- [ ] Empty string / `None` → no exception, function returns silently
- [ ] File that raises `OSError` on `os.remove` → error logged, no exception propagated

### `store_audiocode`

- [ ] Source audio file exists → copied to `"{stem}audiocode_{audio_data}.wav"` beside log file
- [ ] Source audio file does not exist → no file created, no exception raised

### `do_init`

- [ ] Log file does not exist → returns `True`
- [ ] Log file already exists → returns `False`, error logged

### `do_main` (mocked PsychoPy)

- [ ] `psychopy` not installed → returns `-1` without raising
- [ ] With mocked PsychoPy imports: `mode=DEVICES` → returns without opening a window (devices listed to `out_func`)
- [ ] With mocked PsychoPy imports: `mode=BEEP` with `mute=True` → returns `0` without playing sound

---

## Test Infrastructure

- [ ] Create `tests/qr/test_timesync_stimuli.py`
- [ ] No PsychoPy required for pure-utility tests (`get_ts_str`, `get_output_file_name`, `safe_remove`, `store_audiocode`, `do_init`)
- [ ] Mark PsychoPy-dependent tests with `@pytest.mark.requires_psychopy` skip marker
- [ ] Confirm `tests/qr/__init__.py` exists (already present from `bids_inject` tests)

### Coverage targets

| Module | Target | Current |
|---|---|---|
| `qr/timesync_stimuli.py` — utility functions | ≥ 80% | 0% (pending) |
| `qr/timesync_stimuli.py` — overall | ≥ 50% | 0% (pending) |
| `cli/cmd_timesync_stimuli.py` | ≥ 80% | 0% (pending) |

---

## CI/CD Virtual Audio Support

- [x] Add virtual audio (PulseAudio null sink) to `xvfb` mode in `test_reprostim_timesync-stimuli.sh`; switch from `--mute` to `-a psychopy_sounddevice`; record combined audio+video artifact with `ffmpeg`; upload as `reprostim_audiovideo` artifact in `.github/workflows/ci-cd.yml`
- [x] Rename `reprostim_screenshot` artifact/files to `reprostim_audiovideo`; rename `reprostim_psychopy_screenshot.png` to `reprostim_psychopy_image.png`

---

## Open Questions / Future Work

- [x] **PsychoPy headless audio** — `psychopy_sounddevice` works with PulseAudio null sink via `PULSE_SERVER` socket in `/tmp`
- [x] **Container audio passthrough** — implemented via `REPROSTIM_PULSE_SERVER` → `PULSE_SERVER` in `run_reprostim_ci.sh` for both Singularity and Docker
- [ ] **Audio validation in CI** — add ffprobe check that `mp4` artifact contains an audio stream
- [ ] **`DEVICES` mode smoke test** — run `timesync-stimuli -m devices` in CI and assert exit 0
- [ ] **Mock `do_main` for CLI tests** — Click `CliRunner` tests for `cmd_timesync_stimuli.py` (all 13 options)
- [ ] **`interval` mode CI test** — run with `-m interval -x 5` and verify QR codes appear in recording
