# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for the ``bids-qr-inject`` CLI command (Click layer only)."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from reprostim.bids.inject import InjectMode
from reprostim.cli.cmd_bids_qr_inject import bids_qr_inject
from reprostim.cli.entrypoint import main


@pytest.fixture
def inputs(tmp_path):
    """Minimal existing PATHS/--videos inputs (content is irrelevant as
    do_main is mocked)."""
    scans_tsv = tmp_path / "sub-01_ses-01_scans.tsv"
    scans_tsv.write_text("filename\tacq_time\n")
    videos_tsv = tmp_path / "videos.tsv"
    videos_tsv.write_text("")
    return str(scans_tsv), str(videos_tsv)


def _invoke(args, ret=0):
    with patch("reprostim.bids.inject.do_main", return_value=ret) as mock_dm:
        result = CliRunner().invoke(bids_qr_inject, args)
    return result, mock_dm


def test_cli_registered_in_main_group():
    assert main.commands["bids-qr-inject"] is bids_qr_inject


def test_cli_passes_qr_inject_mode(inputs):
    scans_tsv, videos_tsv = inputs
    result, mock_dm = _invoke([scans_tsv, "-f", videos_tsv])
    assert result.exit_code == 0, result.output
    assert mock_dm.call_args.kwargs["inject_mode"] is InjectMode.QR


def test_cli_fixed_values_for_omitted_options(inputs):
    """Omitted bids-inject options are passed to do_main with fixed defaults."""
    scans_tsv, videos_tsv = inputs
    result, mock_dm = _invoke([scans_tsv, "-f", videos_tsv])
    assert result.exit_code == 0, result.output
    kw = mock_dm.call_args.kwargs
    assert kw["buffer_before"] == "0"
    assert kw["buffer_after"] == "0"
    assert kw["buffer_policy"] == "flexible"
    assert kw["qr"] == "none"


@pytest.mark.parametrize(
    "opt",
    [
        ["-q", "auto"],
        ["--qr", "auto"],
        ["-b", "5"],
        ["--buffer-before", "5"],
        ["-a", "5"],
        ["--buffer-after", "5"],
        ["-p", "strict"],
        ["--buffer-policy", "strict"],
    ],
)
def test_cli_omitted_options_rejected(inputs, opt):
    scans_tsv, videos_tsv = inputs
    result, mock_dm = _invoke([scans_tsv, "-f", videos_tsv, *opt])
    assert result.exit_code == 2
    assert "No such option" in result.output
    mock_dm.assert_not_called()


def test_cli_options_forwarded(inputs, tmp_path):
    scans_tsv, videos_tsv = inputs
    result, mock_dm = _invoke(
        [
            scans_tsv,
            "-f",
            videos_tsv,
            "-d",
            str(tmp_path),
            "-r",
            "-t",
            "1.5",
            "-l",
            "top-stimuli",
            "-z",
            "UTC",
            "-Z",
            "UTC",
            "-m",
            "func/",
            "-i",
            "sub-02",
            "-n",
            "-w",
            "force",
            "-k",
            "no",
            "-M",
            "-v",
        ]
    )
    assert result.exit_code == 0, result.output
    kw = mock_dm.call_args.kwargs
    assert kw["paths"] == [scans_tsv]
    assert kw["videos_tsv"] == videos_tsv
    assert kw["dataset_home"] == str(tmp_path)
    assert kw["recursive"] is True
    assert kw["time_offset"] == 1.5
    assert kw["layout"] == "top-stimuli"
    assert kw["reprostim_timezone"] == "UTC"
    assert kw["bids_timezone"] == "UTC"
    assert kw["match"] == "func/"
    assert kw["ignore_paths"] == ["sub-02"]
    assert kw["dry_run"] is True
    assert kw["overwrite"] == "force"
    assert kw["lock"] is False
    assert kw["metadata_only"] is True
    assert kw["verbose"] is True


def test_cli_missing_videos_option_nonzero_exit(inputs):
    scans_tsv, _ = inputs
    result, mock_dm = _invoke([scans_tsv])
    assert result.exit_code != 0
    mock_dm.assert_not_called()


def test_cli_nonzero_do_main_result_propagated_to_exit_code(inputs):
    scans_tsv, videos_tsv = inputs
    result, _ = _invoke([scans_tsv, "-f", videos_tsv], ret=3)
    assert result.exit_code == 3
