# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for reprostim.capture.metadata."""

import json
import pathlib

from reprostim.capture.metadata import (
    MetadataBase,
    MetadataCaptureStop,
    MetadataSessionBegin,
    MetadataSessionEnd,
    find_metadata_by_class,
    find_metadata_json,
    iter_metadata_json,
)

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
    assert results[0]["serial"] == "TESTSERIAL0001"


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


# ===========================================================================
# MetadataSessionBegin / MetadataCaptureStop / MetadataSessionEnd
# ===========================================================================


def test_metadata_session_begin_from_real_sample_log():
    msg = find_metadata_json(str(_SAMPLE_LOG), "type", "session_begin")
    sb = MetadataSessionBegin(**msg)
    assert sb.type == "session_begin"
    assert sb.serial == "TESTSERIAL0001"
    assert sb.vDev == "USB Capture HDMI"
    assert sb.aDev == "hw:3,0"
    # cx/cy are JSON ints in the log; coerced to str
    assert sb.cx == "1920"
    assert sb.cy == "1080"
    assert sb.frameRate == "60"
    # autoRecovery is a JSON bool in the log; coerced to str
    assert sb.autoRecovery == "False"


def test_metadata_capture_stop_from_real_sample_log():
    msg = find_metadata_json(str(_SAMPLE_LOG), "type", "capture_stop")
    cs = MetadataCaptureStop(**msg)
    assert cs.type == "capture_stop"
    assert cs.cap_ts_start == "2025.11.05-14.03.28.837"
    assert cs.cap_ts_stop == "2025.11.05-14.13.47.677"
    assert "Whack resolution" in cs.message


def test_metadata_session_end_from_real_sample_log():
    msg = find_metadata_json(str(_SAMPLE_LOG), "type", "session_end")
    se = MetadataSessionEnd(**msg)
    assert se.type == "session_end"
    assert se.message == "ffmpeg thread terminated"


def test_metadata_base_fields_are_optional():
    assert MetadataSessionBegin().type is None
    assert MetadataCaptureStop().message is None
    assert MetadataSessionEnd().cap_isotime_start is None


# ===========================================================================
# find_metadata_by_class
# ===========================================================================


def test_find_metadata_by_class_session_begin():
    sb = find_metadata_by_class(str(_SAMPLE_LOG), MetadataSessionBegin)
    assert isinstance(sb, MetadataSessionBegin)
    assert sb.type == "session_begin"
    assert sb.serial == "TESTSERIAL0001"
    assert sb.cx == "1920"


def test_find_metadata_by_class_capture_stop():
    cs = find_metadata_by_class(str(_SAMPLE_LOG), MetadataCaptureStop)
    assert isinstance(cs, MetadataCaptureStop)
    assert cs.type == "capture_stop"
    assert "Whack resolution" in cs.message


def test_find_metadata_by_class_session_end():
    se = find_metadata_by_class(str(_SAMPLE_LOG), MetadataSessionEnd)
    assert isinstance(se, MetadataSessionEnd)
    assert se.type == "session_end"
    assert se.message == "ffmpeg thread terminated"


def test_find_metadata_by_class_not_found(tmp_path):
    log = tmp_path / "empty.log"
    log.write_text("no metadata here\n")
    assert find_metadata_by_class(str(log), MetadataSessionBegin) is None


def test_find_metadata_by_class_unknown_class_logs_error_and_returns_none(caplog):
    with caplog.at_level("ERROR"):
        result = find_metadata_by_class(str(_SAMPLE_LOG), MetadataBase)
    assert result is None
    assert "No MetadataType found" in caplog.text
