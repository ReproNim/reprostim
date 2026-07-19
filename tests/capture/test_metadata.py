# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for reprostim.capture.metadata."""

import json
import pathlib

from reprostim.capture.metadata import find_metadata_json, iter_metadata_json

_DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "capture"
_SAMPLE_LOG = _DATA_DIR / "metadata-videocapture.mkv.log"


def _write_log(tmp_path, entries):
    log = tmp_path / "test.log"
    lines = [
        f"PREFIX REPROSTIM-METADATA-JSON: {json.dumps(e)} :REPROSTIM-METADATA-JSON\n"
        for e in entries
    ]
    log.write_text("".join(lines))
    return str(log)


def test_iter_metadata_json_valid(tmp_path):
    path = _write_log(tmp_path, [{"type": "session_begin", "cx": 1920}])
    results = list(iter_metadata_json(path))
    assert len(results) == 1
    assert results[0]["cx"] == 1920


def test_iter_metadata_json_missing_file(tmp_path):
    assert list(iter_metadata_json(str(tmp_path / "missing.log"))) == []


def test_iter_metadata_json_invalid_json(tmp_path):
    """Invalid JSON embedded in a metadata marker line is silently skipped."""
    log = tmp_path / "bad.log"
    log.write_text(
        "PREFIX REPROSTIM-METADATA-JSON: not-valid-json :REPROSTIM-METADATA-JSON\n"
    )
    assert list(iter_metadata_json(str(log))) == []


def test_iter_metadata_json_real_sample_log():
    """Real reprostim-videocapture log with interleaved ffmpeg output around
    the REPROSTIM-METADATA-JSON marker lines."""
    results = list(iter_metadata_json(str(_SAMPLE_LOG)))
    assert [r["type"] for r in results] == [
        "session_begin",
        "capture_stop",
        "session_end",
    ]
    assert results[0]["cx"] == 1920
    assert results[0]["cy"] == 1080
    assert results[0]["serial"] == "D206191219786"


def test_find_metadata_json_found(tmp_path):
    path = _write_log(tmp_path, [{"type": "session_begin", "cx": 1920}])
    result = find_metadata_json(path, "type", "session_begin")
    assert result is not None and result["cx"] == 1920


def test_find_metadata_json_not_found(tmp_path):
    log = tmp_path / "empty.log"
    log.write_text("no metadata here\n")
    assert find_metadata_json(str(log), "type", "session_begin") is None


def test_find_metadata_json_real_sample_log():
    result = find_metadata_json(str(_SAMPLE_LOG), "type", "session_begin")
    assert result is not None
    assert result["vDev"] == "USB Capture HDMI"
    assert result["frameRate"] == "60"
