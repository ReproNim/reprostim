# CLI Exit Code Propagation Specification

## Overview

Reported from real-data testing: on Linux, `reprostim bids-inject` did not
return a non-zero process exit code on failure, even though its underlying
`do_main()` returned a non-zero result. Callers relying on `$?` (cron jobs,
`datalad containers-run`, shell wrappers such as
`code/reprostim-bids-inject`) could not detect failures.

## Root cause

Click's `BaseCommand.main()` runs in `standalone_mode=True` by default (this
is what the `reprostim` console-script entry point — and `python -m
reprostim`, both routing through `cli/entrypoint.py::main` — actually use).
In that mode, `main()` invokes the command callback, captures its return
value, but **discards it**: unless the callback raises an exception or
explicitly calls `ctx.exit(code)` (or `sys.exit(code)`), Click calls
`ctx.exit()` with no argument at the end, which defaults to code `0`.

Concretely: a `@click.command()` callback that ends with `return res` — where
`res` is a non-zero int meant to signal failure — has **no effect on the
process exit code**. The process always exits `0` in standalone mode unless
an exception propagates out of the callback. Verified empirically with a
minimal reproduction (`return 42` from a bare Click command still yields
shell `$? == 0`).

The correct pattern is `ctx.exit(res)`, which raises `click.exceptions.Exit`
— an exception Click's `main()` explicitly catches and turns into
`sys.exit(e.exit_code)`.

## Audit results across `src/reprostim/cli/`

| Command module | Before | After |
|---|---|---|
| `cmd_bids_inject.py` | `return res` | `ctx.exit(res)` |
| `cmd_list_displays.py` | `return res` | `ctx.exit(res)` |
| `cmd_monitor_displays.py` | `return res` | `ctx.exit(res)` |
| `cmd_qr_parse.py` | `return res` | `ctx.exit(res)` |
| `cmd_split_video.py` | `return res` | `ctx.exit(res)` |
| `cmd_timesync_stimuli.py` | `return -1` (on `do_init` failure) and `return res` (final) | `ctx.exit(1)` and `ctx.exit(res)` |
| `cmd_bids_inject_sidecar.py` | already `ctx.exit(res)` | unchanged |
| `cmd_video_audit.py` | already `ctx.exit(1)` / `ctx.exit(rv)` | unchanged |
| `cmd_detect_noscreen.py` | `_main_exit()` helper already calls `sys.exit(code)` directly (the `return code` after it is dead code, but harmless — `sys.exit` raises before it's reached) | unchanged |
| `cmd_echo.py` | no error path (always succeeds) | unchanged |

All 6 affected commands share the same architectural pattern: the Click
callback lazily imports and calls a `do_main(...)`-style function from the
corresponding implementation module, gets back an `int` result, and must
propagate it as the process exit code.

`cmd_timesync_stimuli.py` also had a latent secondary bug on the same error
path: `logger.error()` was called with no message argument, which raises
`TypeError` (stdlib `logging.Logger.error` requires a `msg` positional arg)
instead of logging and returning cleanly. Fixed alongside the exit-code fix
since it's on the exact path being corrected: `logger.error("do_init(...)
failed")`.

## Known non-bug / out of scope

`cmd_list_displays.py` and `cmd_monitor_displays.py` compute `res: int = 0`
as a hardcoded local — `do_list_displays()`/`do_monitor_displays()` in
`capture/disp_mon.py` don't return a status at all (implicit `None`). So
today these two commands can never actually produce a non-zero `res` via the
`ctx.exit(res)` path; a failure inside `do_list_displays`/`do_monitor_displays`
still surfaces correctly as a non-zero exit only because an *uncaught
exception* propagates out of the callback (unrelated to the `return res` vs
`ctx.exit(res)` bug — exceptions always worked). The `ctx.exit(res)` fix is
applied for consistency and to be forward-compatible if these functions ever
gain a real return-code contract, but wiring an actual result code through
`disp_mon.py` is out of scope for this fix.

## Verification approach

Regular unit tests that call `do_main()` directly (bypassing Click) cannot
catch this class of bug — `do_main()` genuinely returns the right int; the
bug is entirely in how the Click callback wrapper handles that int. Tests
must go through `click.testing.CliRunner().invoke(cmd, args)` and assert on
`result.exit_code`, with the underlying `do_main` (or `do_init`) mocked to
return a specific non-zero value, to prove the value actually reaches the
process exit code. This was the exact gap found in the existing test suite:
every existing `CliRunner`-based test mocked `do_main` with `return_value=0`
only — none exercised the non-zero path through the CLI layer.
