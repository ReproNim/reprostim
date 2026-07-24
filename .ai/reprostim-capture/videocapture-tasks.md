# ReproStim VideoCapture Task List

Tracks implementation progress against [videocapture-spec.md](videocapture-spec.md).

Currently, covers only the `usb_scan_mode` (poll/hotplug) feature — see the spec's Open
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
- [ ] Gate the main loop's `findTargetVideoDevice()` call in `CaptureApp.cpp` on the
      selected mode
- [ ] Wire `hotplug` mode: trigger detection from `usbHotplugCallback`/`onUsbDevArrived`/
      `onUsbDevLeft` instead of on every loop tick
- [ ] Manual test: `poll` mode behavior unchanged from current
- [ ] Manual test: `hotplug` mode — device arrival/removal still detected correctly, with
      reduced log volume when nothing changes

---

## Documentation

- [x] `.ai/reprostim-capture/videocapture-spec.md` created (this feature only, for now)
- [x] `.ai/reprostim-capture/videocapture-tasks.md` created (this file)
- [x] `.ai/context.md` — added a bullet for `src/reprostim-capture/videocapture/`
      referencing these docs

---

## Open Questions / Future Work

- [ ] Whether the 1-second `SLEEP_SEC` loop's other responsibilities change in `hotplug`
      mode too
- [ ] Rest of `reprostim-videocapture`'s CLI/config surface remains undocumented under
      `.ai/` — add incrementally
