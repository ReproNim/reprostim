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

The main detection loop in `CaptureApp.cpp` (`do { SLEEP_SEC(1); ... } while(...)`)
unconditionally calls `findTargetVideoDevice()` → `MWRefreshDevice()` every second,
regardless of whether USB device attachment actually changed since the last tick. Over a
long-running session this produces a large volume of `_VERBOSE`/`_INFO` log output, almost
all of it for ticks where nothing happened.

Problem with `dmesg` HID log flood reported in PR [#263](https://github.com/ReproNim/reprostim/issues/263)


Separately, `CaptureApp.cpp` already registers `MWUSBRegisterHotPlug(CaptureApp::usbHotplugCallback,
this)` at startup, and that callback (`usbHotplugCallback` → `onUsbDevArrived`/`onUsbDevLeft`)
already fires on real USB arrival/removal events reported by the Magewell SDK. Today it's
only used to track a "recently disconnected" device set (`disconnDevAdd`/`disconnDevRemove`)
for the poll loop's own bookkeeping — it doesn't drive detection/refresh itself.

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
| `poll`    | **(default)** Unconditional 1-second poll loop calls `MWRefreshDevice()`/`findTargetVideoDevice()` every tick — matches today's behavior, unchanged.          |
| `hotplug` | Detection is driven by the `MWUSBRegisterHotPlug` callback instead — `MWRefreshDevice()`/`findTargetVideoDevice()` is only invoked in response to an actual `USBHOT_PLUG_EVENT_DEVICE_ARRIVED`/`_LEFT` event, not on every loop tick. |

Backed by `UsbScanMode` (`enum class UsbScanMode : int { UNKNOWN = 0, POLL = 1, HOTPLUG =
2, DEFAULT = 1 }`) in `CaptureApp.h`, and parsed via the `parseUsbScanMode(const
std::string&)` helper (declared in `CaptureApp.h`, defined in `CaptureApp.cpp`) — mirrors
the existing `parseLogLevel()` pattern used for `session_logger_level`. An empty/missing
value resolves to `DEFAULT` (`== POLL`); any string other than `"poll"`/`"hotplug"`
(including the redundant literal `"default"`) resolves to `UNKNOWN` and fails
`loadConfig()` with an error — omit the key entirely to get the default instead of
writing it out.

### Affected files

| File | Role |
|------|------|
| `src/reprostim-capture/capturelib/include/reprostim/CaptureApp.h` | *(done)* `UsbScanMode` enum, `AppConfig::usb_scan_mode` field, `parseUsbScanMode()` declaration |
| `src/reprostim-capture/capturelib/src/CaptureApp.cpp` | *(config parsing done, loop-gating not started)* `loadConfig()` parses `usb_scan_mode` into `AppConfig::usb_scan_mode` via `parseUsbScanMode()`. Still TODO: gate the main loop's `findTargetVideoDevice()` call on scan mode; wire `hotplug` mode through `usbHotplugCallback`/`onUsbDevArrived`/`onUsbDevLeft` instead of (or in addition to) today's bookkeeping-only role |
| `src/reprostim-capture/capturelib/src/CaptureLib.cpp` | *(not started)* `findTargetVideoDevice()` — unchanged so far; still the function that calls `MWRefreshDevice()` and looks up the channel, will just be invoked from a different trigger depending on mode |
| `src/reprostim-capture/videocapture/config.yaml` | *(done)* top-level `usb_scan_mode: "poll"` key, documented above |

---

## Open Questions / Future Work

- In `hotplug` mode, does the `do { SLEEP_SEC(1); ... }` loop still need to run every
  second for its other duties (`isSysBreakExec()`, `fConfigChanged`, the
  `disconnDevContains` stop-check), or does something else change there too? Not decided.
- Rest of `reprostim-videocapture`'s CLI/config surface is not documented under `.ai/` yet
  — add incrementally as touched, per the note in Overview.
