# ReproStim VideoCapture Task List

Tracks implementation progress against [videocapture-spec.md](videocapture-spec.md).

Currently, covers only the `usb_scan_mode` (poll/hotplug) feature and its two fixes for
issue #263 (throttled `MWRefreshDevice()`, cached channel handle) — see the spec's Open
Questions for what's still undocumented about the rest of the tool.

---

## USB Scan Mode (`usb_scan_mode`, config-only — no CLI flag)

- [x] Add `UsbScanMode` enum (`UNKNOWN`/`POLL`/`HOTPLUG`/`DEFAULT`) to `CaptureApp.h`
- [x] Add `usb_scan_mode` field to `AppConfig` (`DEFAULT` == `POLL`)
- [x] Add `parseUsbScanMode(const std::string&)` helper — declared in `CaptureApp.h`,
      defined in `CaptureApp.cpp`, mirroring the `parseLogLevel()` pattern
- [x] Parse `usb_scan_mode` from `config.yaml` in `CaptureApp::loadConfig()`; invalid
      values (anything other than `"poll"`/`"hotplug"`, including `"default"`) fail config
      load with an error
- [x] Add `usb_scan_mode: "poll"` to `config.yaml`, placed alongside `device_serial_number`/
      `instance_tag`

---

## Fix 1: throttle `MWRefreshDevice()` (main loop + `findTargetVideoDevice`)

- [x] `findTargetVideoDevice()` (`CaptureLib.h`/`.cpp`) takes a `bool refreshDev=true`
      parameter (default only in the header declaration, matching the `createOutPath`
      convention already used in this file — a duplicated default in the `.cpp` definition
      doesn't compile); gates its own `MWRefreshDevice()` call on it, `MWGetChannelCount()`/
      `MWGetChannelInfoByIndex()` still run unconditionally
- [x] `CaptureApp::checkUsbScan()` added — decides once per tick whether to refresh:
      `poll` always `true`; `hotplug` allows an initial burst of
      `USB_SCAN_HOTPLUG_RETRY_COUNT + 1` ticks after a reset, then throttles to at most once
      per `USB_SCAN_HOTPLUG_INTERVAL_MS` (30 min); `UNKNOWN` always `false`
- [x] `usbScanCount` (`std::atomic<int>`, cross-thread safe) and `lastUsbScanTime`
      (`long long`, main-loop-thread-only) added to `CaptureApp`, reset at `run()` startup
      and on `onUsbDevArrived`/`onUsbDevLeft`
- [x] Main loop calls `checkUsbScan()` once per tick, passes the result through to
      `findTargetVideoDevice(..., fRefreshDev)` as `refreshDev`
- [x] Main loop's other per-tick duties (video signal status, recording start/stop,
      `isSysBreakExec()`/`fConfigChanged`/`disconnDevContains` checks) confirmed to still run
      every tick regardless of scan mode — an earlier draft used `continue` to skip the rest
      of the tick when throttled, which would have broken signal-loss/recording-state
      detection in `hotplug` mode for up to 30 minutes at a stretch; caught in review and
      fixed before merge

---

## Fix 2: cache the channel handle across ticks (`getChannel`/`releaseChannel`)

- [x] `lastChannel` (`HCHANNEL`), `lastChannelDevPath` (`std::string`), `lastChannelReset`
      (`std::atomic<bool>` — written from the `usbHotplugCallback` SDK thread, read from the
      main loop thread) added to `CaptureApp`
- [x] `CaptureApp::getChannel(const std::string& devPath)` added — in `hotplug` mode,
      returns the cached `lastChannel` when `devPath == lastChannelDevPath`, otherwise
      force-closes and reopens; in `poll` mode, always opens fresh (no caching)
- [x] `CaptureApp::releaseChannel(bool forceClose=false)` added — no-op in `hotplug` mode
      unless `forceClose`; always closes (via null-safe `safeMWCloseChannel()`) in `poll`
      mode or when `forceClose=true`
- [x] `CaptureApp::closeChannel()` added (inline in `CaptureApp.h`) as a `releaseChannel(true)`
      alias; declared in the header (an earlier draft defined it out-of-line without a
      header declaration, which doesn't compile) and wired into: `getChannel()` on device
      path change, the `lastChannelReset` handler, and `run()` exit
- [x] Main loop's direct `MWOpenChannelByPath(wPath)` replaced with `getChannel(wPath)`;
      direct `safeMWCloseChannel(hChannel)` at end of tick replaced with `releaseChannel()`
- [x] `onUsbDevArrived`/`onUsbDevLeft` set `lastChannelReset = true`; main loop consumes it
      once per tick at the top, force-closing the cached channel (`hotplug` mode only) so
      the next `getChannel()` call reopens fresh after any USB topology change
- [x] All three new members reset (`lastChannel = NULL`, `lastChannelDevPath.clear()`,
      `lastChannelReset = false`) at `run()` startup, so a config-reload restart starts clean
- [x] `closeChannel()` called once at `run()` exit (after the `do-while` loop), covering both
      graceful shutdown and the config-reload restart path
- [ ] Manual test: `poll` mode behavior unchanged from current (fresh open/close every tick)
- [ ] Manual test: `hotplug` mode — device arrival/removal still detected correctly, no
      `MWRefreshDevice()`/`MWOpenChannelByPath` flood in `dmesg`/`journalctl` when idle
- [ ] Manual test: `hotplug` mode — signal loss / recording stop still detected promptly
      (not delayed by the refresh throttle, per Fix 1's last item above)

---

## Documentation

- [x] `.ai/reprostim-capture/videocapture-spec.md` created (this feature only, for now)
- [x] `.ai/reprostim-capture/videocapture-tasks.md` created (this file)
- [x] `.ai/context.md` — added a bullet for `src/reprostim-capture/videocapture/`
      referencing these docs

---

## Open Questions / Future Work

- [x] Whether the 1-second `SLEEP_SEC` loop's other responsibilities change in `hotplug`
      mode too — resolved, they don't; see Fix 1's last item above
- [ ] `lastChannelReset` fires on any USB hotplug event system-wide, not filtered to the
      target device (`devPath` isn't compared against `targetMwDevPath`/
      `lastChannelDevPath`) — conservative but correct; could filter later if noisy
- [ ] `poll` mode still opens/closes the channel every tick (Fix 2 is `hotplug`-only) —
      intentional (mirrors Fix 1 also being `hotplug`-only), but means `poll` alone doesn't
      resolve the second flood source from #263
- [ ] Rest of `reprostim-videocapture`'s CLI/config surface remains undocumented under
      `.ai/` — add incrementally
