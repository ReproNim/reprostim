# ReproStim VideoCapture Task List

Tracks implementation progress against [videocapture-spec.md](videocapture-spec.md).

Currently, covers only the `--usb-scan-mode` (poll/hotplug) feature — see the spec's Open
Questions for what's still undocumented about the rest of the tool.

---

## USB Scan Mode (`--usb-scan-mode`)

- [ ] Add `usb_scan_mode` field to `AppOpts`/`AppConfig` (`poll` default, `hotplug` alternative)
- [ ] Add `--usb-scan-mode <mode>` to `longOpts`/short-opts string/`HELP_STR` in
      `VideoCapture.cpp::parseOpts`
- [ ] Validate `<mode>` value (`poll`|`hotplug`); error on anything else
- [ ] Gate the main loop's `findTargetVideoDevice()` call in `CaptureApp.cpp` on the
      selected mode
- [ ] Wire `hotplug` mode: trigger detection from `usbHotplugCallback`/`onUsbDevArrived`/
      `onUsbDevLeft` instead of on every loop tick
- [ ] Manual test: `poll` mode behavior unchanged from current
- [ ] Manual test: `hotplug` mode — device arrival/removal still detected correctly, with
      reduced log volume when nothing changes
- [ ] Update `--help`/`HELP_STR` text

---

## Documentation

- [x] `.ai/reprostim-capture/videocapture-spec.md` created (this feature only, for now)
- [x] `.ai/reprostim-capture/videocapture-tasks.md` created (this file)
- [ ] `.ai/context.md` — add a bullet for `src/reprostim-capture/videocapture/` referencing
      these docs (no `.ai/reprostim-capture/` presence existed in context.md before this)

---

## Open Questions / Future Work

- [ ] `config.yaml` equivalent for `usb_scan_mode`? Not decided (see spec)
- [ ] Whether the 1-second `SLEEP_SEC` loop's other responsibilities change in `hotplug`
      mode too
- [ ] Rest of `reprostim-videocapture`'s CLI/config surface remains undocumented under
      `.ai/` — add incrementally
