# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

"""CLI tests (Click CliRunner) for reprostim.cli.cmd_monitor_displays."""

from unittest.mock import patch

from click.testing import CliRunner

from reprostim.cli.cmd_monitor_displays import monitor_displays


def test_cli_help_renders_without_error():
    """--help exits with code 0 and produces output."""
    result = CliRunner().invoke(monitor_displays, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_cli_success_exits_zero():
    """A successful run (do_monitor_displays raises nothing) exits 0."""
    with patch("reprostim.capture.disp_mon.do_monitor_displays") as mock_dmd:
        result = CliRunner().invoke(monitor_displays, [])
    mock_dmd.assert_called_once()
    assert result.exit_code == 0


def test_cli_options_forwarded():
    """CLI options are forwarded positionally to do_monitor_displays."""
    with patch("reprostim.capture.disp_mon.do_monitor_displays") as mock_dmd:
        CliRunner().invoke(
            monitor_displays,
            ["-p", "quartz", "-t", "5", "-w", "10", "-n", "Built-in*", "-i", "1"],
        )
    args = mock_dmd.call_args.args
    assert args[0].value == "quartz"
    assert args[1] == 5
    assert args[2] == 10
    assert args[3] == "Built-in*"
    assert args[4] == "1"


def test_cli_exception_from_implementation_exits_nonzero():
    """An exception raised inside do_monitor_displays surfaces as a non-zero exit.

    Unlike the `return res` bug (a *silently discarded* success/failure
    signal), an uncaught exception has always correctly propagated to a
    non-zero exit code — this test pins down that this remains true after
    the `ctx.exit(res)` fix.
    """
    with patch(
        "reprostim.capture.disp_mon.do_monitor_displays",
        side_effect=RuntimeError("boom"),
    ):
        result = CliRunner().invoke(monitor_displays, [])
    assert result.exit_code != 0
