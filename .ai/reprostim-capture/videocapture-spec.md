# ReproStim VideoCapture Specification

## Overview

`reprostim-videocapture` (`src/reprostim-capture/videocapture/`) is the C++ utility that
records `.mkv` video from a Magewell USB Capture device via `ffmpeg`.

**This spec currently documents only the USB scan mode feature below.** The rest of the
tool's CLI/config surface (recording lifecycle, `ext_proc_opts`, `repromon_opts`, session
logging, etc.) isn't written up here yet — to be added incrementally as it's touched.

---

## USB Scan Mode (`usb_scan_mode`)

### Problem

Issue [#263](https://github.com/ReproNim/reprostim/issues/263) reports `dmesg`/`journalctl`
being flooded with USB HID re-enumeration messages while `reprostim-videocapture` runs.
Root-caused (via discussion on that issue, including two rounds of local testing) to **two
independent APIs** the main detection loop in `CaptureApp.cpp`
(`do { SLEEP_SEC(1); ... } while(...)`) was calling unconditionally on every 1-second tick,
regardless of whether anything had actually changed since the last tick:

1. `findTargetVideoDevice()` → `MWRefreshDevice()` — re-enumerates USB devices.
2. `MWOpenChannelByPath()` + `MWCloseChannel()` — opens/closes the Magewell channel handle
   used for `MWGetVideoSignalStatus()`.

Both fixes below share the same shape: an already-registered mechanism
(`MWUSBRegisterHotPlug(CaptureApp::usbHotplugCallback, this)`, whose callback
`usbHotplugCallback` → `onUsbDevArrived`/`onUsbDevLeft` fires on real USB arrival/removal
events) is used to throttle/cache the expensive call, gated behind the new `usb_scan_mode`
config value — `poll` preserves the original always-refresh/always-reopen behavior exactly,
`hotplug` throttles (1) and caches (2).

### `config.yaml` key: `usb_scan_mode` *(implemented)*

Config-only — no CLI flag. Settable as a top-level scalar, alongside
`device_serial_number`/`instance_tag` (placed right after `instance_tag` in
`config.yaml`):

```yaml
# specify USB scan mode, can be "poll" or "hotplug" or not specified (default is "poll")
usb_scan_mode: "poll"
```

| Value     | Behavior                                                                                                                                                    |
|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `poll`    | **(default)** Every tick unconditionally: `MWRefreshDevice()` runs, and the video channel is opened fresh and closed at the end of the tick. Matches the tool's original behavior exactly, unchanged. |
| `hotplug` | `MWRefreshDevice()` only runs when `checkUsbScan()` says to (see below); the video channel is opened once and kept open across ticks, only reopened when the device path actually changes or a hotplug event fires. |

Backed by `UsbScanMode` (`enum class UsbScanMode : int { UNKNOWN = 0, POLL = 1, HOTPLUG =
2, DEFAULT = 1 }`) in `CaptureApp.h`, and parsed via the `parseUsbScanMode(const
std::string&)` helper (declared in `CaptureApp.h`, defined in `CaptureApp.cpp`) — mirrors
the existing `parseLogLevel()` pattern used for `session_logger_level`. An empty/missing
value resolves to `DEFAULT` (`== POLL`); any string other than `"poll"`/`"hotplug"`
(including the redundant literal `"default"`) resolves to `UNKNOWN` and fails
`loadConfig()` with an error — omit the key entirely to get the default instead of
writing it out.

### Fix 1: throttled `MWRefreshDevice()` via `checkUsbScan()`

`CaptureApp::checkUsbScan()` decides, once per loop tick, whether this tick should call
`MWRefreshDevice()` (via `findTargetVideoDevice(..., refreshDev)`, see below):

- `poll` mode: always returns `true` — unthrottled, matches original behavior.
- `hotplug` mode: returns `true` for the first `USB_SCAN_HOTPLUG_RETRY_COUNT + 1` ticks
  after a reset (an initial "burst" — see `usbScanCount`, reset to `0` on
  `onUsbDevArrived`/`onUsbDevLeft` and at `run()` startup), then throttles to at most once
  per `USB_SCAN_HOTPLUG_INTERVAL_MS` (30 minutes) via `lastUsbScanTime`. Returns `false`
  otherwise (skip the refresh this tick).
- `UNKNOWN` mode (defensive, shouldn't normally be reachable — `loadConfig()` rejects it
  outright): always returns `false`.

`findTargetVideoDevice(const std::string &serialNumber, VideoDevice &vd, bool
refreshDev=true)` (`CaptureLib.h`/`.cpp`) takes the `checkUsbScan()` result as `refreshDev`:
when `true`, calls `MWRefreshDevice()` as before; when `false`, skips it and just queries
`MWGetChannelCount()`/`MWGetChannelInfoByIndex()` against the SDK's already-cached device
list from the last actual refresh. The default (`refreshDev=true`) matches the tool's
original always-refresh behavior, so any future caller that doesn't pass the argument
explicitly gets the safe/old behavior, not silently-skip-refresh.

Critically, only the `MWRefreshDevice()` call is gated — the rest of the loop (video
signal status check, recording start/stop, `onCaptureStop`/`onCaptureIdle`) still runs
every tick regardless of `checkUsbScan()`'s answer, so `hotplug` mode doesn't fall behind
on detecting signal loss or recording state changes; only the noisy re-enumeration is
throttled.

### Fix 2: cached channel handle via `getChannel()`/`releaseChannel()`

Three new `CaptureApp` members support this: `lastChannel` (`HCHANNEL`), `lastChannelDevPath`
(`std::string`), and `lastChannelReset` (`std::atomic<bool>`, since it's written from the
`usbHotplugCallback` SDK thread and read from the main loop thread).

- **`HCHANNEL CaptureApp::getChannel(const std::string& devPath)`** — replaces the direct
  `MWOpenChannelByPath(wPath)` call in the main loop. In `hotplug` mode: if `devPath`
  matches `lastChannelDevPath` (the device instance hasn't changed since the last open),
  returns the cached `lastChannel` without reopening; otherwise force-closes any cached
  handle (`closeChannel()`) and opens a fresh one. In `poll` mode: always opens a fresh
  channel (no caching), matching original behavior.
- **`void CaptureApp::releaseChannel(bool forceClose=false)`** — replaces the direct
  `safeMWCloseChannel(hChannel)` call at the end of each tick. In `hotplug` mode with
  `forceClose=false` (the loop's normal end-of-tick call), it's a no-op — the channel stays
  open for reuse next tick. With `forceClose=true`, or in `poll` mode regardless of the
  argument, it actually closes the cached handle via `safeMWCloseChannel()` (null-safe,
  idempotent) and clears `lastChannelDevPath`.
- **`void CaptureApp::closeChannel()`** *(inline, in `CaptureApp.h`)* — convenience alias
  for `releaseChannel(true)`, used at the three points a cached channel must be force-closed
  regardless of mode: inside `getChannel()` when the device path changes, when
  `lastChannelReset` is consumed at the top of the loop (see below), and once at `run()`
  exit (covers both graceful shutdown and the config-reload restart path).
- **`lastChannelReset`** — set to `true` by both `onUsbDevArrived` and `onUsbDevLeft` (the
  hotplug callback fires for *any* USB topology change system-wide, not filtered to the
  target device specifically — see Open Questions). Consumed once per tick at the top of
  the main loop: if set, cleared, and (in `hotplug` mode only) `closeChannel()` is called so
  the next `getChannel()` call reopens fresh rather than trusting a possibly-stale cached
  handle across a USB event.

All three new members are reset (`lastChannel = NULL`, `lastChannelDevPath.clear()`,
`lastChannelReset = false`) at the top of `run()`, so a config-reload restart (which
constructs a fresh loop iteration but reuses the same `CaptureApp` instance's `run()` call)
starts with clean channel-cache state.

### Affected files

| File | Role |
|------|------|
| `src/reprostim-capture/capturelib/include/reprostim/CaptureApp.h` | *(done)* `UsbScanMode` enum; `AppConfig::usb_scan_mode` field; `parseUsbScanMode()` declaration; `USB_SCAN_HOTPLUG_RETRY_COUNT`/`USB_SCAN_HOTPLUG_INTERVAL_MS` constants; new `CaptureApp` members `lastChannel`/`lastChannelDevPath`/`lastChannelReset`/`lastUsbScanTime`/`usbScanCount`; new method declarations `checkUsbScan()`, `getChannel()`, `releaseChannel()`; inline `closeChannel()` |
| `src/reprostim-capture/capturelib/src/CaptureApp.cpp` | *(done)* `loadConfig()` parses `usb_scan_mode`; `checkUsbScan()`, `getChannel()`, `releaseChannel()` implemented; main loop gates `findTargetVideoDevice()`'s refresh and replaces direct `MWOpenChannelByPath`/`safeMWCloseChannel` calls with `getChannel()`/`releaseChannel()`; `onUsbDevArrived`/`onUsbDevLeft` reset `usbScanCount` and set `lastChannelReset` |
| `src/reprostim-capture/capturelib/src/CaptureLib.cpp` | *(done)* `findTargetVideoDevice()` takes `bool refreshDev` (default `true` in the header), gates its own `MWRefreshDevice()` call on it — channel lookup (`MWGetChannelCount()`/`MWGetChannelInfoByIndex()`) still runs unconditionally either way |
| `src/reprostim-capture/videocapture/config.yaml` | *(done)* top-level `usb_scan_mode: "poll"` key, documented above |

---

## Open Questions / Future Work

- Resolved: the loop's other per-tick duties (video signal status, recording start/stop,
  `isSysBreakExec()`, `fConfigChanged`, the `disconnDevContains` stop-check) all still run
  every tick regardless of scan mode — only the `MWRefreshDevice()` call and the
  channel open/close are gated. An earlier draft of this fix used `continue` to skip the
  whole rest of the tick when `checkUsbScan()` returned `false`, which would have broken
  signal-loss/recording-state detection for up to 30 minutes at a stretch in `hotplug`
  mode; corrected before merge.
- `lastChannelReset` is set on *any* USB hotplug event system-wide (the `devPath` passed to
  `onUsbDevArrived`/`onUsbDevLeft` isn't compared against `targetMwDevPath`/
  `lastChannelDevPath`), so an unrelated USB peripheral connecting/disconnecting on the same
  host will still force a channel reopen next tick. Correct, just more conservative than the
  theoretical minimum — could be refined later to filter by `devPath` if it proves noisy in
  practice.
- `poll` mode still opens/closes the channel every tick (Fix 2 only applies in `hotplug`
  mode) — intentional, mirroring how `MWRefreshDevice()` throttling is also `hotplug`-only,
  but means selecting `poll` (the default) does not address the second flood source from
  #263, only `hotplug` does.
- Rest of `reprostim-videocapture`'s CLI/config surface is not documented under `.ai/` yet
  — add incrementally as touched, per the note in Overview.
