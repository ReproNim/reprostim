# ReproStim VideoCapture Specification

## Overview

`reprostim-videocapture` (`src/reprostim-capture/videocapture/`) is the C++ utility that
records `.mkv` video from a Magewell USB Capture device via `ffmpeg`.

**This spec currently documents only the USB scan mode feature below.** The rest of the
tool's CLI/config surface (recording lifecycle, `ext_proc_opts`, `repromon_opts`, session
logging, etc.) isn't written up here yet — to be added incrementally as it's touched.

---

## USB Scan Mode (`--usb-scan-mode`)

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

### New CLI option: `--usb-scan-mode <mode>`

| Value     | Behavior                                                                                                                                                    |
|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `poll`    | **(default)** Unconditional 1-second poll loop calls `MWRefreshDevice()`/`findTargetVideoDevice()` every tick — matches today's behavior, unchanged.          |
| `hotplug` | Detection is driven by the `MWUSBRegisterHotPlug` callback instead — `MWRefreshDevice()`/`findTargetVideoDevice()` is only invoked in response to an actual `USBHOT_PLUG_EVENT_DEVICE_ARRIVED`/`_LEFT` event, not on every loop tick. |

Shape follows the existing `-e/--ext-proc <mode>` (`all|status|exec`, default `status`) and
`-l/--list-devices <devices>` (`all|audio|video`, default `all`) options already in
`VideoCapture.cpp::parseOpts` — same `--<name> <mode>`/documented-default style.

### Affected files

| File | Role |
|------|------|
| `src/reprostim-capture/videocapture/src/VideoCapture.cpp` | `parseOpts` — add `--usb-scan-mode` to `longOpts`/short-opts string/`HELP_STR`; `AppOpts`/`AppConfig` gets the new field carrying the selected mode |
| `src/reprostim-capture/capturelib/src/CaptureApp.cpp` | Main detection loop (`do { SLEEP_SEC(1); ... }`) — gate the `findTargetVideoDevice()` call on scan mode; `usbHotplugCallback`/`onUsbDevArrived`/`onUsbDevLeft` — in `hotplug` mode, trigger detection from here instead of (or in addition to) today's bookkeeping-only role |
| `src/reprostim-capture/capturelib/src/CaptureLib.cpp` | `findTargetVideoDevice()` — unchanged; still the function that calls `MWRefreshDevice()` and looks up the channel, just invoked from a different trigger depending on mode |
| `src/reprostim-capture/videocapture/config.yaml` | Possible YAML config key (e.g. top-level `usb_scan_mode: "poll"`, alongside `device_serial_number`/`instance_tag`) — not yet decided, see Open Questions |

---

## Open Questions / Future Work

- Whether `usb_scan_mode` should also be settable via `config.yaml`. Most top-level CLI
  options here (`-o`/`-d`/`-c`) are process-invocation-only with no YAML equivalent, but
  some features (`ext_proc_opts`, `repromon_opts`) do have a dedicated YAML section — TBD
  which pattern this follows.
- In `hotplug` mode, does the `do { SLEEP_SEC(1); ... }` loop still need to run every
  second for its other duties (`isSysBreakExec()`, `fConfigChanged`, the
  `disconnDevContains` stop-check), or does something else change there too? Not decided.
- Rest of `reprostim-videocapture`'s CLI/config surface is not documented under `.ai/` yet
  — add incrementally as touched, per the note in Overview.
