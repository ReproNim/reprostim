# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

"""CLI tests (Click CliRunner) for reprostim.cli.cmd_list_displays."""

from unittest.mock import patch

from click.testing import CliRunner

from reprostim.cli.cmd_list_displays import list_displays


def test_cli_help_renders_without_error():
    """--help exits with code 0 and produces output."""
    result = CliRunner().invoke(list_displays, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_cli_success_exits_zero():
    """A successful run (do_list_displays raises nothing) exits 0."""
    with patch("reprostim.capture.disp_mon.do_list_displays") as mock_dld:
        result = CliRunner().invoke(list_displays, [])
    mock_dld.assert_called_once()
    assert result.exit_code == 0


def test_cli_options_forwarded():
    """-p/--provider and -f/--format are forwarded to do_list_displays."""
    with patch("reprostim.capture.disp_mon.do_list_displays") as mock_dld:
        CliRunner().invoke(list_displays, ["-p", "pygame", "-f", "text"])
    args = mock_dld.call_args.args
    assert args[0].value == "pygame"
    assert args[1] == "text"


def test_cli_exception_from_implementation_exits_nonzero():
    """An exception raised inside do_list_displays surfaces as a non-zero exit.

    Unlike the `return res` bug (a *silently discarded* success/failure
    signal), an uncaught exception has always correctly propagated to a
    non-zero exit code — this test pins down that this remains true after
    the `ctx.exit(res)` fix.
    """
    with patch(
        "reprostim.capture.disp_mon.do_list_displays",
        side_effect=RuntimeError("boom"),
    ):
        result = CliRunner().invoke(list_displays, [])
    assert result.exit_code != 0
