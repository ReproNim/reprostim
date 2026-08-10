# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

"""CLI tests (Click CliRunner) for reprostim.cli.cmd_timesync_stimuli."""

from unittest.mock import patch

from click.testing import CliRunner

from reprostim.cli.cmd_timesync_stimuli import timesync_stimuli


def test_cli_help_renders_without_error():
    """--help exits with code 0 and produces output."""
    result = CliRunner().invoke(timesync_stimuli, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_cli_do_init_failure_exits_nonzero():
    """do_init() returning False must produce a non-zero exit code.

    Regression test: this path used to `return -1` from the Click
    callback, which Click's standalone-mode main() silently discards
    (the process exits 0 regardless of the returned value unless an
    exception is raised or ctx.exit()/sys.exit() is called explicitly).
    """
    with (
        patch("reprostim.qr.timesync_stimuli.do_init", return_value=False),
        patch("reprostim.qr.timesync_stimuli.do_main") as mock_do_main,
    ):
        result = CliRunner().invoke(timesync_stimuli, [])
    mock_do_main.assert_not_called()
    assert result.exit_code != 0


def test_cli_nonzero_do_main_result_propagated_to_exit_code():
    """A non-zero do_main() result must become the process exit code.

    Regression test: the command used to `return res` from the Click
    callback at the very end, silently discarded by Click's standalone
    main() the same way as the `return -1` case above.
    """
    with (
        patch("reprostim.qr.timesync_stimuli.do_init", return_value=True),
        patch("reprostim.qr.timesync_stimuli.do_main", return_value=4),
    ):
        result = CliRunner().invoke(timesync_stimuli, [])
    assert result.exit_code == 4


def test_cli_success_exits_zero():
    """do_init() True and do_main() returning 0 exits 0 (baseline)."""
    with (
        patch("reprostim.qr.timesync_stimuli.do_init", return_value=True),
        patch("reprostim.qr.timesync_stimuli.do_main", return_value=0),
    ):
        result = CliRunner().invoke(timesync_stimuli, [])
    assert result.exit_code == 0
