# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""CLI tests for ``reprostim video-audit``.

Covers: --nosignal-opts, --qr-opts, --config and their default behaviour.
``do_main`` is patched so no real video processing takes place.
"""

from unittest.mock import patch

import click.testing
import pytest

from reprostim.cli.cmd_video_audit import video_audit

runner = click.testing.CliRunner()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_mkv(tmp_path):
    """Return a path to an empty .mkv file accepted by click.Path(exists=True)."""
    p = tmp_path / "test.mkv"
    p.touch()
    return str(p)


def _invoke(args):
    """Invoke the video_audit command and return the result."""
    return runner.invoke(video_audit, args, catch_exceptions=False)


# ---------------------------------------------------------------------------
# --help
# ---------------------------------------------------------------------------


def test_help_renders():
    """--help exits cleanly and lists all key options."""
    result = runner.invoke(video_audit, ["--help"])
    assert result.exit_code == 0
    for flag in ("--nosignal-opts", "--qr-opts", "--config", "--mode", "--audit-src"):
        assert flag in result.output


# ---------------------------------------------------------------------------
# --nosignal-opts / -n
# ---------------------------------------------------------------------------


def test_nosignal_opts_forwarded(tmp_mkv):
    """-n / --nosignal-opts value is forwarded to do_main as nosignal_opts kwarg."""
    opts = "--number-of-checks 200 --threshold 0.9"
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-n", opts, tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["nosignal_opts"] == opts


def test_nosignal_opts_short_form_forwarded(tmp_mkv):
    """Short form -n is accepted and forwards the value identically
    to --nosignal-opts."""
    opts = "--number-of-checks 50"
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["--nosignal-opts", opts, tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["nosignal_opts"] == opts


def test_nosignal_opts_default_is_none(tmp_mkv):
    """Omitting --nosignal-opts passes nosignal_opts=None so VaContext uses
    built-in defaults."""
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke([tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["nosignal_opts"] is None


# ---------------------------------------------------------------------------
# --qr-opts / -q
# ---------------------------------------------------------------------------


def test_qr_opts_forwarded(tmp_mkv):
    """-q / --qr-opts value is forwarded to do_main as qr_opts kwarg."""
    opts = "--skip 2 --std-threshold 15"
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-q", opts, tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["qr_opts"] == opts


def test_qr_opts_short_form_forwarded(tmp_mkv):
    """Short form -q is accepted and forwards the value identically to --qr-opts."""
    opts = "--skip 4"
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["--qr-opts", opts, tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["qr_opts"] == opts


def test_qr_opts_default_is_none(tmp_mkv):
    """Omitting --qr-opts passes qr_opts=None so no extra options are forwarded."""
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke([tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["qr_opts"] is None


# ---------------------------------------------------------------------------
# -c / --config
# ---------------------------------------------------------------------------


def test_config_nosignal_opts(tmp_path, tmp_mkv):
    """nosignal-opts from config file is forwarded to do_main as nosignal_opts."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("nosignal-opts: '--number-of-checks 300 --threshold 0.8'\n")
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-c", str(cfg), tmp_mkv])
    assert result.exit_code == 0
    assert (
        mock_do_main.call_args.kwargs["nosignal_opts"]
        == "--number-of-checks 300 --threshold 0.8"
    )


def test_config_qr_opts(tmp_path, tmp_mkv):
    """qr-opts from config file is forwarded to do_main as qr_opts."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("qr-opts: '--skip 3 --std-threshold 20'\n")
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-c", str(cfg), tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["qr_opts"] == "--skip 3 --std-threshold 20"


def test_config_cli_overrides_nosignal_opts(tmp_path, tmp_mkv):
    """Explicit -n on CLI takes precedence over nosignal-opts in config."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("nosignal-opts: '--number-of-checks 300'\n")
    cli_opts = "--number-of-checks 999"
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-c", str(cfg), "-n", cli_opts, tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["nosignal_opts"] == cli_opts


def test_config_cli_overrides_qr_opts(tmp_path, tmp_mkv):
    """Explicit -q on CLI takes precedence over qr-opts in config."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("qr-opts: '--skip 3'\n")
    cli_opts = "--skip 99"
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-c", str(cfg), "-q", cli_opts, tmp_mkv])
    assert result.exit_code == 0
    assert mock_do_main.call_args.kwargs["qr_opts"] == cli_opts


def test_config_other_keys(tmp_path, tmp_mkv):
    """mode, recursive, and max-files from config are passed correctly to do_main."""
    from reprostim.qr.video_audit import VaMode

    cfg = tmp_path / "config.yaml"
    cfg.write_text("mode: full\nrecursive: true\nmax-files: 5\n")
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-c", str(cfg), tmp_mkv])
    assert result.exit_code == 0
    args = mock_do_main.call_args.args
    assert args[2] is True  # recursive
    assert args[3] == VaMode.FULL  # mode
    assert args[5] == 5  # max_files


def test_config_audit_src_list(tmp_path, tmp_mkv):
    """audit-src list in config is converted to a set of VaSource values."""
    from reprostim.qr.video_audit import VaSource

    cfg = tmp_path / "config.yaml"
    cfg.write_text("audit-src:\n  - internal\n  - qr\n")
    with patch("reprostim.qr.video_audit.do_main") as mock_do_main:
        result = _invoke(["-c", str(cfg), tmp_mkv])
    assert result.exit_code == 0
    va_src = mock_do_main.call_args.args[4]
    assert va_src == {VaSource.INTERNAL, VaSource.QR}
