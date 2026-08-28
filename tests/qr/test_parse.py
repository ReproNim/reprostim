# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for CLI option handling in ``reprostim.qr.parse``.

Covers: --grayscale, --std-threshold, --scale, --skip, --qr-decoder,
--video-decoder, --qrdet, --qrdet-model-size, --qr-decoder-workers,
--start-time, --end-time.

qrdet tests use mocks only — no real GPU or qrdet/torch packages required.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import click.testing
import cv2
import numpy as np
import pytest

import reprostim.qr.parse as qp_mod
from reprostim.cli.cmd_qr_parse import qr_parse as qr_parse_cmd
from reprostim.qr.parse import (
    Grayscale,
    InfoSummary,
    ParseContext,
    ParseSummary,
    QrDecoder,
    VideoDecoder,
    _decode_qr_opencv,
    _decode_qr_pyzbar,
    _init_qrdet,
    _qrdet_filter,
    do_info,
    do_info_file,
    do_main,
    do_parse,
    get_video_time_info,
    resolve_video_time_info,
)
from reprostim.video.media_info import AudioInfo
from reprostim.video.media_info import VideoInfo as FfprobeVideoInfo

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Validly-named video file matching get_video_time_info pattern
_VIDEO_NAME = "2025.01.01-00.00.00.000--2025.01.01-00.01.00.000.mkv"


def _blank_frame(h: int = 64, w: int = 64) -> np.ndarray:
    """Return a solid-black BGR frame."""
    return np.zeros((h, w, 3), dtype=np.uint8)


def _make_mock_cap(frames: list, fps: float = 30.0) -> MagicMock:
    """Return a mock ``cv2.VideoCapture`` that yields *frames* then EOF."""
    cap = MagicMock()
    cap.isOpened.return_value = True
    cap.get.side_effect = lambda prop: {
        cv2.CAP_PROP_FRAME_COUNT: float(len(frames)),
        cv2.CAP_PROP_FPS: fps,
        cv2.CAP_PROP_FRAME_WIDTH: 64.0,
        cv2.CAP_PROP_FRAME_HEIGHT: 64.0,
    }.get(prop, 0.0)
    cap.read.side_effect = [(True, f) for f in frames] + [(False, None)]
    return cap


def _run_parse(ctx: ParseContext, frames: list, video_path: str) -> list:
    """Drive ``do_parse`` with a mocked video; return all yielded items."""
    with patch("cv2.VideoCapture", return_value=_make_mock_cap(frames)):
        return list(do_parse(ctx, video_path))


def _video(tmp_path) -> str:
    """Create an empty file with a valid timestamp name and return its path."""
    p = tmp_path / _VIDEO_NAME
    p.touch()
    return str(p)


def _video_named(tmp_path, name: str) -> str:
    """Create an empty file with an arbitrary *name* and return its path."""
    p = tmp_path / name
    p.touch()
    return str(p)


# ===========================================================================
# ParseContext — defaults
# ===========================================================================


def test_parse_context_defaults():
    """ParseContext has the expected default values for all options."""
    ctx = ParseContext()
    assert ctx.grayscale == Grayscale.OPENCV
    assert ctx.scale == 1.0
    assert ctx.skip == 0
    assert ctx.std_threshold == 10.0
    assert ctx.qr_decoder == QrDecoder.PYZBAR
    assert ctx.video_decoder == VideoDecoder.OPENCV
    assert ctx.qrdet is False
    assert ctx.qrdet_model_size == "s"
    assert ctx.start_time_opt == "auto"
    assert ctx.end_time_opt == "auto"


# ===========================================================================
# --grayscale
# ===========================================================================


def test_grayscale_opencv_calls_cvtcolor(tmp_path):
    """--grayscale opencv: cv2.cvtColor(frame, COLOR_BGR2GRAY) is called."""
    ctx = ParseContext(
        grayscale=Grayscale.OPENCV, std_threshold=0, qr_decoder=QrDecoder.PYZBAR
    )
    with patch("reprostim.qr.parse.decode", return_value=[]), patch(
        "cv2.cvtColor", wraps=cv2.cvtColor
    ) as mock_cvt:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    calls = [
        c
        for c in mock_cvt.call_args_list
        if len(c.args) > 1 and c.args[1] == cv2.COLOR_BGR2GRAY
    ]
    assert calls, "cv2.cvtColor(frame, COLOR_BGR2GRAY) was not called"


def test_grayscale_numpy_skips_cvtcolor(tmp_path):
    """--grayscale numpy: cv2.cvtColor is not called."""
    ctx = ParseContext(
        grayscale=Grayscale.NUMPY, std_threshold=0, qr_decoder=QrDecoder.PYZBAR
    )
    with patch("reprostim.qr.parse.decode", return_value=[]), patch(
        "cv2.cvtColor"
    ) as mock_cvt:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_cvt.assert_not_called()


def test_grayscale_none_skips_cvtcolor(tmp_path):
    """--grayscale none: cv2.cvtColor is not called; raw frame passes through."""
    ctx = ParseContext(
        grayscale=Grayscale.NONE, std_threshold=0, qr_decoder=QrDecoder.PYZBAR
    )
    with patch("reprostim.qr.parse.decode", return_value=[]), patch(
        "cv2.cvtColor"
    ) as mock_cvt:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_cvt.assert_not_called()


# ===========================================================================
# --std-threshold
# ===========================================================================


def test_std_threshold_zero_disables_filter(tmp_path):
    """--std-threshold 0: cv2.meanStdDev is not called; all frames reach decoder."""
    ctx = ParseContext(std_threshold=0, qr_decoder=QrDecoder.PYZBAR)
    with patch("reprostim.qr.parse.decode", return_value=[]), patch(
        "cv2.meanStdDev"
    ) as mock_std:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_std.assert_not_called()


def test_std_threshold_skips_low_std_frames(tmp_path):
    """--std-threshold 40: frames with std < 40 do not reach QR decoder."""
    ctx = ParseContext(std_threshold=40.0, qr_decoder=QrDecoder.PYZBAR)
    low_std = (np.array([[0.0]]), np.array([[5.0]]))  # 5.0 < 40.0
    with patch("cv2.meanStdDev", return_value=low_std), patch(
        "reprostim.qr.parse._decode_qr"
    ) as mock_decode:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_decode.assert_not_called()


def test_std_threshold_passes_high_std_frames(tmp_path):
    """--std-threshold 40: frames with std >= 40 reach the QR decoder."""
    ctx = ParseContext(std_threshold=40.0, qr_decoder=QrDecoder.PYZBAR)
    high_std = (np.array([[0.0]]), np.array([[50.0]]))  # 50.0 >= 40.0
    with patch("cv2.meanStdDev", return_value=high_std), patch(
        "reprostim.qr.parse._decode_qr", return_value=None
    ) as mock_decode:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_decode.assert_called_once()


# ===========================================================================
# --scale
# ===========================================================================


def test_scale_half_calls_resize(tmp_path):
    """--scale 0.5: cv2.resize is called with fx=0.5, fy=0.5."""
    ctx = ParseContext(scale=0.5, std_threshold=0, qr_decoder=QrDecoder.PYZBAR)
    with patch("reprostim.qr.parse.decode", return_value=[]), patch(
        "cv2.resize", wraps=cv2.resize
    ) as mock_resize:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_resize.assert_called_once()
    assert mock_resize.call_args.kwargs["fx"] == 0.5
    assert mock_resize.call_args.kwargs["fy"] == 0.5


def test_scale_one_skips_resize(tmp_path):
    """--scale 1.0 (default): cv2.resize is not called."""
    ctx = ParseContext(scale=1.0, std_threshold=0, qr_decoder=QrDecoder.PYZBAR)
    with patch("reprostim.qr.parse.decode", return_value=[]), patch(
        "cv2.resize"
    ) as mock_resize:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_resize.assert_not_called()


# ===========================================================================
# --skip
# ===========================================================================


def test_skip_zero_processes_all_frames(tmp_path):
    """--skip 0: every frame reaches _decode_qr."""
    ctx = ParseContext(skip=0, std_threshold=0, qr_decoder=QrDecoder.PYZBAR)
    with patch("reprostim.qr.parse._decode_qr", return_value=None) as mock_decode:
        _run_parse(ctx, [_blank_frame()] * 3, _video(tmp_path))
    assert mock_decode.call_count == 3


def test_skip_two_processes_every_third_frame(tmp_path):
    """--skip 2: 1 of every 3 frames reaches _decode_qr (2 out of 6)."""
    ctx = ParseContext(skip=2, std_threshold=0, qr_decoder=QrDecoder.PYZBAR)
    with patch("reprostim.qr.parse._decode_qr", return_value=None) as mock_decode:
        _run_parse(ctx, [_blank_frame()] * 6, _video(tmp_path))
    assert mock_decode.call_count == 2


# ===========================================================================
# --qr-decoder
# ===========================================================================


def test_qr_decoder_none_skips_decode(tmp_path):
    """--qr-decoder none: _decode_qr is never called."""
    ctx = ParseContext(qr_decoder=QrDecoder.NONE, std_threshold=0)
    with patch("reprostim.qr.parse._decode_qr") as mock_decode:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_decode.assert_not_called()


def test_qr_decoder_pyzbar_calls_pyzbar_decode(tmp_path):
    """--qr-decoder pyzbar: pyzbar.decode is called (default backend)."""
    ctx = ParseContext(qr_decoder=QrDecoder.PYZBAR, std_threshold=0)
    with patch("reprostim.qr.parse.decode", return_value=[]) as mock_decode:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_decode.assert_called()


def test_qr_decoder_opencv_calls_qrcode_detector(tmp_path):
    """--qr-decoder opencv: cv2.QRCodeDetector().detectAndDecode is called."""
    ctx = ParseContext(qr_decoder=QrDecoder.OPENCV, std_threshold=0)
    mock_det = MagicMock()
    mock_det.detectAndDecode.return_value = ("", None, None)
    with patch("cv2.QRCodeDetector", return_value=mock_det):
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_det.detectAndDecode.assert_called()


# ===========================================================================
# --video-decoder
# ===========================================================================


def test_video_decoder_opencv_uses_cv2_video_capture(tmp_path):
    """--video-decoder opencv: cv2.VideoCapture is constructed with the video path."""
    video = _video(tmp_path)
    ctx = ParseContext(
        video_decoder=VideoDecoder.OPENCV, std_threshold=0, qr_decoder=QrDecoder.NONE
    )
    with patch("cv2.VideoCapture", return_value=_make_mock_cap([])) as mock_cap:
        list(do_parse(ctx, video))
    mock_cap.assert_called_once_with(video)


# ===========================================================================
# --qrdet / --qrdet-model-size  (mocked — no real GPU or qrdet required)
# ===========================================================================


@pytest.fixture(autouse=False)
def reset_qrdet_detector():
    """Reset the module-level _qrdet_detector before and after each qrdet test."""
    qp_mod._qrdet_detector = None
    yield
    qp_mod._qrdet_detector = None


def test_qrdet_filter_none_detector_always_passes(reset_qrdet_detector):
    """_qrdet_filter returns True when no detector is initialised."""
    assert qp_mod._qrdet_detector is None
    assert _qrdet_filter(_blank_frame()) is True


def test_qrdet_filter_with_region_found(reset_qrdet_detector):
    """_qrdet_filter returns True when detector.detect finds a QR region."""
    mock_det = MagicMock()
    mock_det.detect.return_value = [{"bbox_xyxy": [0, 0, 10, 10]}]
    qp_mod._qrdet_detector = mock_det
    frame = _blank_frame()
    assert _qrdet_filter(frame) is True
    mock_det.detect.assert_called_once_with(image=frame, is_bgr=True)


def test_qrdet_filter_no_region_returns_false(reset_qrdet_detector):
    """_qrdet_filter returns False when detector.detect finds no QR region."""
    mock_det = MagicMock()
    mock_det.detect.return_value = []
    qp_mod._qrdet_detector = mock_det
    assert _qrdet_filter(_blank_frame()) is False


def test_init_qrdet_disabled_sets_global_none(reset_qrdet_detector):
    """_init_qrdet with qrdet=False sets _qrdet_detector to None."""
    _init_qrdet(ParseContext(qrdet=False))
    assert qp_mod._qrdet_detector is None


def test_init_qrdet_missing_packages_raises_importerror(reset_qrdet_detector):
    """_init_qrdet raises ImportError with install hint when qrdet is unavailable."""
    ctx = ParseContext(qrdet=True)
    with patch.dict("sys.modules", {"qrdet": None}):
        with pytest.raises(ImportError, match=r"pip install reprostim\[gpu\]"):
            _init_qrdet(ctx)


def test_init_qrdet_model_size_passed_to_constructor(reset_qrdet_detector):
    """_init_qrdet passes qrdet_model_size to QRDetector(model_size=...)."""
    ctx = ParseContext(qrdet=True, qrdet_model_size="n")
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False
    mock_qrdet_pkg = MagicMock()
    with patch.dict("sys.modules", {"torch": mock_torch, "qrdet": mock_qrdet_pkg}):
        _init_qrdet(ctx)
    mock_qrdet_pkg.QRDetector.assert_called_once_with(model_size="n")


def test_do_main_qrdet_missing_packages_returns_error(tmp_path):
    """do_main returns 1 and logs an error when --qrdet is set but qrdet unavailable."""
    video = _video(tmp_path)
    with patch.dict("sys.modules", {"qrdet": None}):
        result = do_main(path=video, mode="PARSE", qrdet=True)
    assert result == 1


# ===========================================================================
# --qr-decoder-workers
# ===========================================================================


def test_qr_decoder_workers_default_is_zero():
    """ParseContext default qr_decoder_workers is 0 (sequential)."""
    ctx = ParseContext()
    assert ctx.qr_decoder_workers == 0


def test_qr_decoder_workers_zero_does_not_use_thread_pool(tmp_path):
    """--qr-decoder-workers 0: ThreadPoolExecutor is not instantiated."""
    ctx = ParseContext(qr_decoder_workers=0, std_threshold=0, qr_decoder=QrDecoder.NONE)
    with patch("reprostim.qr.parse.ThreadPoolExecutor") as mock_pool:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_pool.assert_not_called()


def test_qr_decoder_workers_one_does_not_use_thread_pool(tmp_path):
    """--qr-decoder-workers 1: ThreadPoolExecutor is not instantiated
    (threshold is > 1)."""
    ctx = ParseContext(qr_decoder_workers=1, std_threshold=0, qr_decoder=QrDecoder.NONE)
    with patch("reprostim.qr.parse.ThreadPoolExecutor") as mock_pool:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_pool.assert_not_called()


def test_qr_decoder_workers_parallel_uses_thread_pool(tmp_path):
    """--qr-decoder-workers 4: ThreadPoolExecutor is instantiated with max_workers=4."""
    ctx = ParseContext(qr_decoder_workers=4, std_threshold=0, qr_decoder=QrDecoder.NONE)
    with patch(
        "reprostim.qr.parse.ThreadPoolExecutor", wraps=ThreadPoolExecutor
    ) as mock_pool:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_pool.assert_called_once_with(max_workers=4)


def test_qr_decoder_workers_parallel_processes_all_frames(tmp_path):
    """--qr-decoder-workers 4: _process_frame is called once per non-skipped frame."""
    frames = [_blank_frame()] * 5
    ctx = ParseContext(
        qr_decoder_workers=4, std_threshold=0, qr_decoder=QrDecoder.PYZBAR
    )
    with patch("reprostim.qr.parse._process_frame", return_value=None) as mock_pf:
        _run_parse(ctx, frames, _video(tmp_path))
    assert mock_pf.call_count == len(frames)


def test_qr_decoder_workers_parallel_output_matches_sequential(tmp_path):
    """--qr-decoder-workers 4: QrRecords and ParseSummary match the sequential path."""
    frames = [_blank_frame()] * 6
    # _process_frame returns QR data for frames 1-3, None for the rest.
    # All three return the same payload so the state machine collapses them
    # to one record.
    qr_data = {
        "time_formatted": "2025-01-01T00:00:01",
        "keys_time_str": "2025-01-01T00:00:01",
    }
    per_frame = [qr_data, qr_data, qr_data, None, None, None]

    ctx_seq = ParseContext(
        qr_decoder_workers=0, std_threshold=0, qr_decoder=QrDecoder.PYZBAR
    )
    ctx_par = ParseContext(
        qr_decoder_workers=4, std_threshold=0, qr_decoder=QrDecoder.PYZBAR
    )

    with patch("reprostim.qr.parse._process_frame", side_effect=list(per_frame)):
        seq_items = _run_parse(ctx_seq, frames, _video(tmp_path))

    with patch("reprostim.qr.parse._process_frame", side_effect=list(per_frame)):
        par_items = _run_parse(ctx_par, frames, _video(tmp_path))

    seq_records = [i for i in seq_items if not isinstance(i, ParseSummary)]
    par_records = [i for i in par_items if not isinstance(i, ParseSummary)]

    assert len(seq_records) == len(par_records)
    for s, p in zip(seq_records, par_records):
        assert s.data == p.data
        assert s.frame_start == p.frame_start
        assert s.time_start == p.time_start


# ===========================================================================
# get_video_time_info — edge cases
# ===========================================================================

_QR_DATA = {
    "time_formatted": "2025-01-01T00:00:01",
    "keys_time_str": "2025-01-01T00:00:01",
}


def test_get_video_time_info_invalid_filename():
    """Completely unrecognised filename returns success=False."""
    vti = get_video_time_info("not_a_valid_name.mkv")
    assert not vti.success
    assert vti.error is not None


def test_get_video_time_info_start_only_filename():
    """Filename with start timestamp only (no end) returns success=False but
    sets start_time."""
    # pattern2b: YYYY.MM.DD-HH.MM.SS.mmm--.ext
    vti = get_video_time_info("2025.01.01-00.00.00.000--.mkv")
    assert not vti.success
    assert vti.start_time is not None
    assert vti.end_time is None


def test_get_video_time_info_start_gte_end():
    """Filename where start >= end returns success=False."""
    vti = get_video_time_info("2025.01.01-00.01.00.000--2025.01.01-00.00.00.000.mkv")
    assert not vti.success
    assert "not earlier" in vti.error


# ===========================================================================
# resolve_video_time_info — -S/--start-time / -E/--end-time resolution
# ===========================================================================


def test_resolve_auto_auto_matching_filename(tmp_path):
    """auto/auto with a filename that matches the pattern behaves exactly like
    plain get_video_time_info (backward-compatible default)."""
    vti = resolve_video_time_info(_video(tmp_path), "auto", "auto")
    assert vti.success
    assert vti.start_time == datetime(2025, 1, 1, 0, 0, 0)
    assert vti.end_time == datetime(2025, 1, 1, 0, 1, 0)
    assert vti.duration_sec == pytest.approx(60.0)


def test_resolve_filename_filename_matching(tmp_path):
    """filename/filename with a matching filename extracts both from it."""
    vti = resolve_video_time_info(_video(tmp_path), "filename", "filename")
    assert vti.success
    assert vti.start_time == datetime(2025, 1, 1, 0, 0, 0)
    assert vti.end_time == datetime(2025, 1, 1, 0, 1, 0)


def test_resolve_filename_mode_non_matching_fails(tmp_path):
    """filename/filename against a non-conforming filename fails with a clear
    error, not an exception."""
    path = _video_named(tmp_path, "not_a_valid_name.mkv")
    vti = resolve_video_time_info(path, "filename", "filename")
    assert not vti.success
    assert "does not match" in vti.error


def test_resolve_start_filename_partial_pattern_succeeds(tmp_path):
    """Regression: -S filename against a start-only ("in-progress recording")
    filename succeeds using the available start, even though the overall
    get_video_time_info() match is only partial (success=False there)."""
    path = _video_named(tmp_path, "2025.01.01-00.00.00.000--.mkv")
    mtime_dt = datetime(2026, 1, 1, 12, 0, 0)
    with patch(
        "reprostim.qr.parse.os.path.getmtime", return_value=mtime_dt.timestamp()
    ):
        vti = resolve_video_time_info(path, "filename", "auto")
    assert vti.success
    assert vti.start_time == datetime(2025, 1, 1, 0, 0, 0)
    assert vti.end_time == mtime_dt


def test_resolve_end_filename_partial_pattern_fails(tmp_path):
    """-E filename against a start-only filename fails: fn_end is genuinely
    unavailable, regardless of fn_start being present."""
    path = _video_named(tmp_path, "2025.01.01-00.00.00.000--.mkv")
    vti = resolve_video_time_info(path, "auto", "filename")
    assert not vti.success
    assert "does not match" in vti.error


def test_resolve_auto_fallback_non_matching_filename(tmp_path):
    """auto/auto against a non-conforming filename: end falls back to mtime,
    start falls back to end - real (ffprobe) duration."""
    path = _video_named(tmp_path, "some_other_tool_export.mp4")
    mtime_dt = datetime(2026, 1, 1, 12, 0, 0)
    fake_vi = FfprobeVideoInfo(duration_sec=90.0)
    with patch(
        "reprostim.qr.parse.os.path.getmtime", return_value=mtime_dt.timestamp()
    ), patch("reprostim.qr.parse.check_ffprobe", return_value=True), patch(
        "reprostim.qr.parse.get_audio_video_info_ffprobe",
        return_value=(AudioInfo(), fake_vi),
    ):
        vti = resolve_video_time_info(path, "auto", "auto")
    assert vti.success
    assert vti.end_time == mtime_dt
    assert vti.start_time == mtime_dt - timedelta(seconds=90.0)
    assert vti.duration_sec == pytest.approx(90.0)


def test_resolve_auto_fallback_ffprobe_missing(tmp_path):
    """auto start fallback fails cleanly when ffprobe is not installed."""
    path = _video_named(tmp_path, "some_other_tool_export.mp4")
    with patch("reprostim.qr.parse.check_ffprobe", return_value=False):
        vti = resolve_video_time_info(path, "auto", "auto")
    assert not vti.success
    assert "ffprobe" in vti.error.lower()


def test_resolve_auto_fallback_ffprobe_duration_unavailable(tmp_path):
    """auto start fallback fails cleanly when ffprobe can't determine duration."""
    path = _video_named(tmp_path, "some_other_tool_export.mp4")
    fake_vi = FfprobeVideoInfo(duration_sec=None)
    with patch("reprostim.qr.parse.check_ffprobe", return_value=True), patch(
        "reprostim.qr.parse.get_audio_video_info_ffprobe",
        return_value=(AudioInfo(), fake_vi),
    ):
        vti = resolve_video_time_info(path, "auto", "auto")
    assert not vti.success
    assert "duration" in vti.error.lower()


def test_resolve_explicit_iso_both_valid(tmp_path):
    """Explicit ISO 8601 for both, in valid order: used verbatim."""
    vti = resolve_video_time_info(
        _video(tmp_path), "2025-06-01T10:00:00", "2025-06-01T11:00:00"
    )
    assert vti.success
    assert vti.start_time == datetime(2025, 6, 1, 10, 0, 0)
    assert vti.end_time == datetime(2025, 6, 1, 11, 0, 0)
    assert vti.duration_sec == pytest.approx(3600.0)


def test_resolve_explicit_iso_both_inverted_fails(tmp_path):
    """Explicit ISO 8601 for both, in inverted order: chronological validation
    fails since both were given explicitly via the CLI."""
    vti = resolve_video_time_info(
        _video(tmp_path), "2025-06-01T11:00:00", "2025-06-01T10:00:00"
    )
    assert not vti.success
    assert "must be <=" in vti.error


def test_resolve_explicit_iso_malformed_start(tmp_path):
    """Malformed --start-time value fails cleanly, no exception raised."""
    vti = resolve_video_time_info(_video(tmp_path), "not-a-date", "auto")
    assert not vti.success
    assert "Invalid --start-time value" in vti.error


def test_resolve_explicit_iso_malformed_end(tmp_path):
    """Malformed --end-time value fails cleanly, no exception raised."""
    vti = resolve_video_time_info(_video(tmp_path), "auto", "not-a-date")
    assert not vti.success
    assert "Invalid --end-time value" in vti.error


def test_resolve_validation_skipped_when_only_one_side_explicit(tmp_path):
    """Chronological validation only applies when *both* -S/-E are explicit —
    an explicit start after the filename/auto-derived end is accepted
    (a deliberate scope limit, not a bug)."""
    vti = resolve_video_time_info(_video(tmp_path), "2025-06-01T00:00:00", "auto")
    assert vti.success
    assert vti.end_time == datetime(2025, 1, 1, 0, 1, 0)  # from filename
    assert vti.duration_sec < 0  # inverted, but not validated — by design


def test_resolve_explicit_start_auto_end_uses_filename(tmp_path):
    """Explicit --start-time with --end-time auto: end still resolves from a
    matching filename."""
    vti = resolve_video_time_info(_video(tmp_path), "2024-12-31T00:00:00", "auto")
    assert vti.success
    assert vti.start_time == datetime(2024, 12, 31, 0, 0, 0)
    assert vti.end_time == datetime(2025, 1, 1, 0, 1, 0)


# ===========================================================================
# _decode_qr_pyzbar / _decode_qr_opencv — found path
# ===========================================================================


def test_decode_qr_pyzbar_returns_dict_when_found():
    """_decode_qr_pyzbar returns a dict when pyzbar finds a QR code."""
    payload = {"key": "value"}
    mock_result = MagicMock()
    mock_result.data = repr(repr(payload).encode("utf-8")).encode("utf-8")
    # Simulate what pyzbar returns: bytes of repr of repr of dict
    mock_result.data = str(repr(payload).encode("utf-8"))
    # Use a simpler mock: data bytes that eval correctly
    encoded = repr(payload).encode("utf-8")
    mock_result.data = encoded
    with patch("reprostim.qr.parse.decode", return_value=[mock_result]):
        result = _decode_qr_pyzbar(_blank_frame())
    assert result == payload


def test_decode_qr_opencv_returns_dict_when_found():
    """_decode_qr_opencv returns a dict when OpenCV finds a QR code."""
    payload = {"key": "value"}
    mock_det = MagicMock()
    mock_det.detectAndDecode.return_value = (repr(payload), None, None)
    with patch("cv2.QRCodeDetector", return_value=mock_det):
        result = _decode_qr_opencv(_blank_frame())
    assert result == payload


def test_decode_qr_opencv_returns_none_when_not_found():
    """_decode_qr_opencv returns None when OpenCV finds no QR code."""
    mock_det = MagicMock()
    mock_det.detectAndDecode.return_value = ("", None, None)
    with patch("cv2.QRCodeDetector", return_value=mock_det):
        result = _decode_qr_opencv(_blank_frame())
    assert result is None


# ===========================================================================
# _qr_state_machine — transition between two different QR codes
# ===========================================================================


def test_qr_state_machine_two_different_qr_codes(tmp_path):
    """Two distinct QR payloads in sequence produce two separate QrRecords."""
    qr_a = dict(_QR_DATA)
    qr_b = {
        "time_formatted": "2025-01-01T00:00:02",
        "keys_time_str": "2025-01-01T00:00:02",
    }
    # frames: [a, a, b, b, None]
    per_frame = [qr_a, qr_a, qr_b, qr_b, None]
    ctx = ParseContext(std_threshold=0, qr_decoder=QrDecoder.PYZBAR)
    with patch("reprostim.qr.parse._process_frame", side_effect=list(per_frame)):
        items = _run_parse(ctx, [_blank_frame()] * len(per_frame), _video(tmp_path))
    records = [i for i in items if not isinstance(i, ParseSummary)]
    assert len(records) == 2
    assert records[0].data == qr_a
    assert records[1].data == qr_b


def test_qr_state_machine_qr_at_end_of_video(tmp_path):
    """A QR code that runs to the last frame is still yielded."""
    per_frame = [None, _QR_DATA, _QR_DATA]
    ctx = ParseContext(std_threshold=0, qr_decoder=QrDecoder.PYZBAR)
    with patch("reprostim.qr.parse._process_frame", side_effect=list(per_frame)):
        items = _run_parse(ctx, [_blank_frame()] * len(per_frame), _video(tmp_path))
    records = [i for i in items if not isinstance(i, ParseSummary)]
    assert len(records) == 1
    assert records[0].data == _QR_DATA


# ===========================================================================
# do_parse — special branches
# ===========================================================================


def test_do_parse_summary_only(tmp_path):
    """summary_only=True yields only a ParseSummary with exit_code=0, no QrRecords."""
    ctx = ParseContext(std_threshold=0, qr_decoder=QrDecoder.NONE)
    with patch("cv2.VideoCapture", return_value=_make_mock_cap([_blank_frame()])):
        items = list(do_parse(ctx, _video(tmp_path), summary_only=True))
    assert len(items) == 1
    assert isinstance(items[0], ParseSummary)
    assert items[0].exit_code == 0


def test_do_parse_invalid_filename_ignore_errors(tmp_path):
    """do_parse with invalid filename and ignore_errors=True still opens the video."""
    bad_path = str(tmp_path / "invalid_name.mkv")
    open(bad_path, "w").close()
    ctx = ParseContext(std_threshold=0, qr_decoder=QrDecoder.NONE)
    with patch("cv2.VideoCapture", return_value=_make_mock_cap([])):
        # summary_only stops before the vti.duration_sec comparison that would
        # crash when the filename couldn't be parsed (duration_sec=None)
        items = list(do_parse(ctx, bad_path, ignore_errors=True, summary_only=True))
    assert any(isinstance(i, ParseSummary) for i in items)


def test_do_parse_video_not_opened(tmp_path):
    """do_parse yields nothing when VideoCapture fails to open."""
    ctx = ParseContext(std_threshold=0, qr_decoder=QrDecoder.NONE)
    cap = MagicMock()
    cap.isOpened.return_value = False
    with patch("cv2.VideoCapture", return_value=cap):
        items = list(do_parse(ctx, _video(tmp_path)))
    assert items == []


# ===========================================================================
# do_info / do_info_file
# ===========================================================================


def test_do_info_file_returns_summary(tmp_path):
    """do_info_file returns an InfoSummary with path and size populated."""
    video = _video(tmp_path)
    summary, _ = do_info_file(video)
    assert isinstance(summary, InfoSummary)
    assert summary.path == video
    assert summary.size_mb is not None


def test_do_info_yields_for_file(tmp_path):
    """do_info yields one InfoSummary for a file path."""
    items = list(do_info(_video(tmp_path)))
    assert len(items) == 1


def test_do_info_yields_for_directory(tmp_path):
    """do_info yields one InfoSummary per .mkv file in a directory."""
    (tmp_path / _VIDEO_NAME).touch()
    (tmp_path / "other.txt").touch()
    items = list(do_info(str(tmp_path)))
    assert len(items) == 1


def test_do_info_invalid_path(tmp_path):
    """do_info yields nothing for a non-existent path."""
    items = list(do_info(str(tmp_path / "nonexistent")))
    assert items == []


# ===========================================================================
# do_main — validation and mode dispatch
# ===========================================================================


def test_do_main_path_not_found(tmp_path):
    """do_main returns 1 when the path does not exist."""
    result = do_main(path=str(tmp_path / "missing.mkv"), mode="PARSE")
    assert result == 1


def test_do_main_invalid_scale(tmp_path):
    """do_main returns 1 for scale outside (0, 1]."""
    result = do_main(path=_video(tmp_path), mode="PARSE", scale=0.0)
    assert result == 1


def test_do_main_invalid_skip(tmp_path):
    """do_main returns 1 for skip < 0."""
    result = do_main(path=_video(tmp_path), mode="PARSE", skip=-1)
    assert result == 1


def test_do_main_unknown_mode(tmp_path):
    """do_main returns -1 for an unrecognised mode."""
    result = do_main(path=_video(tmp_path), mode="UNKNOWN")
    assert result == -1


def test_do_main_info_mode(tmp_path):
    """do_main INFO mode calls out_func for each InfoSummary."""
    out = []
    result = do_main(path=_video(tmp_path), mode="INFO", out_func=out.append)
    assert result == 0
    assert len(out) == 1


def test_do_main_parse_mode_success(tmp_path):
    """do_main PARSE mode returns 0 and calls out_func with each JSON record."""
    out = []
    ctx_holder = {}

    def fake_do_parse(ctx, path, **_kwargs):
        ctx_holder["ctx"] = ctx
        ps = ParseSummary()
        ps.exit_code = 0
        yield ps

    with patch("reprostim.qr.parse.do_parse", side_effect=fake_do_parse):
        result = do_main(path=_video(tmp_path), mode="PARSE", out_func=out.append)
    assert result == 0
    assert len(out) == 1


def test_do_main_invalid_start_time(tmp_path):
    """do_main returns 1 for a malformed --start-time value in PARSE mode."""
    result = do_main(path=_video(tmp_path), mode="PARSE", start_time="not-a-date")
    assert result == 1


def test_do_main_invalid_end_time(tmp_path):
    """do_main returns 1 for a malformed --end-time value in PARSE mode."""
    result = do_main(path=_video(tmp_path), mode="PARSE", end_time="not-a-date")
    assert result == 1


def test_do_main_info_mode_ignores_start_end_time(tmp_path):
    """INFO mode is unaffected by -S/-E — no validation, no effect, even with
    a malformed value that would fail in PARSE mode."""
    out = []
    result = do_main(
        path=_video(tmp_path),
        mode="INFO",
        start_time="not-a-date",
        end_time="not-a-date",
        out_func=out.append,
    )
    assert result == 0
    assert len(out) == 1


def test_do_main_start_end_time_forwarded_to_parse_context(tmp_path):
    """do_main forwards start_time/end_time into ParseContext, which do_parse
    then reads for time resolution."""
    ctx_holder = {}

    def fake_do_parse(ctx, path, **_kwargs):
        ctx_holder["ctx"] = ctx
        ps = ParseSummary()
        ps.exit_code = 0
        yield ps

    with patch("reprostim.qr.parse.do_parse", side_effect=fake_do_parse):
        do_main(
            path=_video(tmp_path),
            mode="PARSE",
            start_time="2025-01-01T00:00:00",
            end_time="2025-01-01T00:01:00",
        )
    assert ctx_holder["ctx"].start_time_opt == "2025-01-01T00:00:00"
    assert ctx_holder["ctx"].end_time_opt == "2025-01-01T00:01:00"


# ===========================================================================
# cmd_qr_parse CLI — Click runner tests
# ===========================================================================


@pytest.fixture
def cli_runner():
    return click.testing.CliRunner()


def test_cli_parse_mode_success(cli_runner, tmp_path):
    """CLI PARSE mode exits 0 when do_main succeeds."""
    video = _video(tmp_path)
    with patch("reprostim.qr.parse.do_main", return_value=0):
        result = cli_runner.invoke(qr_parse_cmd, [str(video)])
    assert result.exit_code == 0


def test_cli_info_mode(cli_runner, tmp_path):
    """CLI --mode INFO is forwarded to do_main."""
    video = _video(tmp_path)
    with patch("reprostim.qr.parse.do_main", return_value=0) as mock_main:
        cli_runner.invoke(qr_parse_cmd, ["--mode", "INFO", str(video)])
    assert mock_main.call_args.kwargs["mode"] == "INFO"


def test_cli_options_forwarded(cli_runner, tmp_path):
    """CLI options are forwarded correctly to do_main."""
    video = _video(tmp_path)
    with patch("reprostim.qr.parse.do_main", return_value=0) as mock_main:
        cli_runner.invoke(
            qr_parse_cmd,
            [
                "--grayscale",
                "numpy",
                "--scale",
                "0.5",
                "--skip",
                "2",
                "--std-threshold",
                "20.0",
                "--qr-decoder",
                "opencv",
                "--qr-decoder-workers",
                "4",
                "--start-time",
                "2025-01-01T00:00:00",
                "--end-time",
                "filename",
                str(video),
            ],
        )
    kw = mock_main.call_args.kwargs
    assert kw["grayscale"] == "numpy"
    assert kw["scale"] == 0.5
    assert kw["skip"] == 2
    assert kw["std_threshold"] == 20.0
    assert kw["qr_decoder"] == "opencv"
    assert kw["qr_decoder_workers"] == 4
    assert kw["start_time"] == "2025-01-01T00:00:00"
    assert kw["end_time"] == "filename"


def test_cli_start_end_time_default_is_auto(cli_runner, tmp_path):
    """-S/-E default to "auto" when not specified on the CLI."""
    video = _video(tmp_path)
    with patch("reprostim.qr.parse.do_main", return_value=0) as mock_main:
        cli_runner.invoke(qr_parse_cmd, [str(video)])
    kw = mock_main.call_args.kwargs
    assert kw["start_time"] == "auto"
    assert kw["end_time"] == "auto"


def test_cli_invalid_path(cli_runner, tmp_path):
    """CLI exits non-zero for a path that does not exist."""
    result = cli_runner.invoke(qr_parse_cmd, [str(tmp_path / "missing.mkv")])
    assert result.exit_code != 0


def test_cli_nonzero_do_main_result_propagated_to_exit_code(cli_runner, tmp_path):
    """A non-zero do_main() result must become the process exit code.

    Regression test: the command used to `return res` from the Click
    callback, which Click's standalone-mode main() silently discards
    (the process exits 0 no matter what `res` was, unless an exception
    is raised or ctx.exit()/sys.exit() is called explicitly).
    """
    video = _video(tmp_path)
    with patch("reprostim.qr.parse.do_main", return_value=7):
        result = cli_runner.invoke(qr_parse_cmd, [str(video)])
    assert result.exit_code == 7
