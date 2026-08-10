# CLI Exit Code Propagation Task List

Tracks implementation progress against [exit-codes-spec.md](exit-codes-spec.md).

---

## Fixes

- [x] `src/reprostim/cli/cmd_bids_inject.py` — `return res` → `ctx.exit(res)`
- [x] `src/reprostim/cli/cmd_list_displays.py` — `return res` → `ctx.exit(res)`
- [x] `src/reprostim/cli/cmd_monitor_displays.py` — `return res` → `ctx.exit(res)`
- [x] `src/reprostim/cli/cmd_qr_parse.py` — `return res` → `ctx.exit(res)`
- [x] `src/reprostim/cli/cmd_split_video.py` — `return res` → `ctx.exit(res)`
- [x] `src/reprostim/cli/cmd_timesync_stimuli.py` — `return -1` → `ctx.exit(1)` (`do_init`
      failure path) and `return res` → `ctx.exit(res)` (final); also fixed the adjacent
      `logger.error()` call (was missing its required `msg` argument, which raised `TypeError`
      instead of logging)
- [x] Confirmed already correct, no change needed: `cmd_bids_inject_sidecar.py`
      (`ctx.exit(res)`), `cmd_video_audit.py` (`ctx.exit(1)` / `ctx.exit(rv)`),
      `cmd_detect_noscreen.py` (`_main_exit()` helper calls `sys.exit(code)` directly),
      `cmd_echo.py` (no error path)

## Tests

- [x] `tests/qr/test_parse.py::test_cli_nonzero_do_main_result_propagated_to_exit_code` —
      mocks `do_main` to return `7`, asserts `CliRunner` `result.exit_code == 7`
- [x] `tests/video/test_split.py::test_cli_nonzero_do_main_result_propagated_to_exit_code` —
      mocks `do_main` to return `(5, [])`, asserts `result.exit_code == 5`
- [x] `tests/bids/test_inject.py` — new CLI test section added (none existed before, despite
      this being the module where the bug was found in production):
      `test_cli_help_renders_without_error`, `test_cli_missing_videos_option_nonzero_exit`,
      `test_cli_nonzero_do_main_result_propagated_to_exit_code` (mocks `do_main` → `3`, asserts
      `result.exit_code == 3`), `test_cli_zero_do_main_result_exits_zero`
- [x] `tests/cli/` package created (no CLI-level tests existed at all for these 3 commands):
  - [x] `test_cmd_list_displays.py` — `--help`, success (mocked `do_list_displays`), option
        forwarding, exception-from-implementation still exits non-zero
  - [x] `test_cmd_monitor_displays.py` — same shape as above for `do_monitor_displays`
  - [x] `test_cmd_timesync_stimuli.py` — `--help`,
        `test_cli_do_init_failure_exits_nonzero` (regression test for the `return -1` bug),
        `test_cli_nonzero_do_main_result_propagated_to_exit_code` (regression test for the
        `return res` bug), baseline success case
- [x] Full suite run (`pytest tests/`): 733 passed, 1 pre-existing unrelated failure
      (`tests/qr/test_parse.py::test_do_main_qrdet_missing_packages_returns_error` — a
      `torch.overrides` double-docstring `RuntimeError` in this environment; confirmed via
      `git stash` that it fails identically on unmodified code, unrelated to this change)

## Docs

- [x] `.ai/cli/exit-codes-spec.md` created
- [x] `.ai/cli/exit-codes-tasks.md` created (this file)
- [x] `.ai/context.md` — cli/ section updated to link this spec
