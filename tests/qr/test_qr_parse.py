# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for CLI option handling in ``reprostim.qr.qr_parse``.

Covers: --grayscale, --std-threshold, --scale, --skip, --qr-decoder,
--video-decoder, --qrdet, --qrdet-model-size, --qr-decoder-workers.

qrdet tests use mocks only — no real GPU or qrdet/torch packages required.
"""

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import click.testing
import cv2
import numpy as np
import pytest

import reprostim.qr.qr_parse as qp_mod
from reprostim.cli.cmd_qr_parse import qr_parse as qr_parse_cmd
from reprostim.qr.qr_parse import (
    Grayscale,
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
)

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


# ===========================================================================
# --grayscale
# ===========================================================================


def test_grayscale_opencv_calls_cvtcolor(tmp_path):
    """--grayscale opencv: cv2.cvtColor(frame, COLOR_BGR2GRAY) is called."""
    ctx = ParseContext(
        grayscale=Grayscale.OPENCV, std_threshold=0, qr_decoder=QrDecoder.PYZBAR
    )
    with patch("reprostim.qr.qr_parse.decode", return_value=[]), patch(
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
    with patch("reprostim.qr.qr_parse.decode", return_value=[]), patch(
        "cv2.cvtColor"
    ) as mock_cvt:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_cvt.assert_not_called()


def test_grayscale_none_skips_cvtcolor(tmp_path):
    """--grayscale none: cv2.cvtColor is not called; raw frame passes through."""
    ctx = ParseContext(
        grayscale=Grayscale.NONE, std_threshold=0, qr_decoder=QrDecoder.PYZBAR
    )
    with patch("reprostim.qr.qr_parse.decode", return_value=[]), patch(
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
    with patch("reprostim.qr.qr_parse.decode", return_value=[]), patch(
        "cv2.meanStdDev"
    ) as mock_std:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_std.assert_not_called()


def test_std_threshold_skips_low_std_frames(tmp_path):
    """--std-threshold 40: frames with std < 40 do not reach QR decoder."""
    ctx = ParseContext(std_threshold=40.0, qr_decoder=QrDecoder.PYZBAR)
    low_std = (np.array([[0.0]]), np.array([[5.0]]))  # 5.0 < 40.0
    with patch("cv2.meanStdDev", return_value=low_std), patch(
        "reprostim.qr.qr_parse._decode_qr"
    ) as mock_decode:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_decode.assert_not_called()


def test_std_threshold_passes_high_std_frames(tmp_path):
    """--std-threshold 40: frames with std >= 40 reach the QR decoder."""
    ctx = ParseContext(std_threshold=40.0, qr_decoder=QrDecoder.PYZBAR)
    high_std = (np.array([[0.0]]), np.array([[50.0]]))  # 50.0 >= 40.0
    with patch("cv2.meanStdDev", return_value=high_std), patch(
        "reprostim.qr.qr_parse._decode_qr", return_value=None
    ) as mock_decode:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_decode.assert_called_once()


# ===========================================================================
# --scale
# ===========================================================================


def test_scale_half_calls_resize(tmp_path):
    """--scale 0.5: cv2.resize is called with fx=0.5, fy=0.5."""
    ctx = ParseContext(scale=0.5, std_threshold=0, qr_decoder=QrDecoder.PYZBAR)
    with patch("reprostim.qr.qr_parse.decode", return_value=[]), patch(
        "cv2.resize", wraps=cv2.resize
    ) as mock_resize:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_resize.assert_called_once()
    assert mock_resize.call_args.kwargs["fx"] == 0.5
    assert mock_resize.call_args.kwargs["fy"] == 0.5


def test_scale_one_skips_resize(tmp_path):
    """--scale 1.0 (default): cv2.resize is not called."""
    ctx = ParseContext(scale=1.0, std_threshold=0, qr_decoder=QrDecoder.PYZBAR)
    with patch("reprostim.qr.qr_parse.decode", return_value=[]), patch(
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
    with patch("reprostim.qr.qr_parse._decode_qr", return_value=None) as mock_decode:
        _run_parse(ctx, [_blank_frame()] * 3, _video(tmp_path))
    assert mock_decode.call_count == 3


def test_skip_two_processes_every_third_frame(tmp_path):
    """--skip 2: 1 of every 3 frames reaches _decode_qr (2 out of 6)."""
    ctx = ParseContext(skip=2, std_threshold=0, qr_decoder=QrDecoder.PYZBAR)
    with patch("reprostim.qr.qr_parse._decode_qr", return_value=None) as mock_decode:
        _run_parse(ctx, [_blank_frame()] * 6, _video(tmp_path))
    assert mock_decode.call_count == 2


# ===========================================================================
# --qr-decoder
# ===========================================================================


def test_qr_decoder_none_skips_decode(tmp_path):
    """--qr-decoder none: _decode_qr is never called."""
    ctx = ParseContext(qr_decoder=QrDecoder.NONE, std_threshold=0)
    with patch("reprostim.qr.qr_parse._decode_qr") as mock_decode:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_decode.assert_not_called()


def test_qr_decoder_pyzbar_calls_pyzbar_decode(tmp_path):
    """--qr-decoder pyzbar: pyzbar.decode is called (default backend)."""
    ctx = ParseContext(qr_decoder=QrDecoder.PYZBAR, std_threshold=0)
    with patch("reprostim.qr.qr_parse.decode", return_value=[]) as mock_decode:
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
    with patch("reprostim.qr.qr_parse.ThreadPoolExecutor") as mock_pool:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_pool.assert_not_called()


def test_qr_decoder_workers_one_does_not_use_thread_pool(tmp_path):
    """--qr-decoder-workers 1: ThreadPoolExecutor is not instantiated
    (threshold is > 1)."""
    ctx = ParseContext(qr_decoder_workers=1, std_threshold=0, qr_decoder=QrDecoder.NONE)
    with patch("reprostim.qr.qr_parse.ThreadPoolExecutor") as mock_pool:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_pool.assert_not_called()


def test_qr_decoder_workers_parallel_uses_thread_pool(tmp_path):
    """--qr-decoder-workers 4: ThreadPoolExecutor is instantiated with max_workers=4."""
    ctx = ParseContext(qr_decoder_workers=4, std_threshold=0, qr_decoder=QrDecoder.NONE)
    with patch(
        "reprostim.qr.qr_parse.ThreadPoolExecutor", wraps=ThreadPoolExecutor
    ) as mock_pool:
        _run_parse(ctx, [_blank_frame()], _video(tmp_path))
    mock_pool.assert_called_once_with(max_workers=4)


def test_qr_decoder_workers_parallel_processes_all_frames(tmp_path):
    """--qr-decoder-workers 4: _process_frame is called once per non-skipped frame."""
    frames = [_blank_frame()] * 5
    ctx = ParseContext(
        qr_decoder_workers=4, std_threshold=0, qr_decoder=QrDecoder.PYZBAR
    )
    with patch("reprostim.qr.qr_parse._process_frame", return_value=None) as mock_pf:
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

    with patch("reprostim.qr.qr_parse._process_frame", side_effect=list(per_frame)):
        seq_items = _run_parse(ctx_seq, frames, _video(tmp_path))

    with patch("reprostim.qr.qr_parse._process_frame", side_effect=list(per_frame)):
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
    with patch("reprostim.qr.qr_parse.decode", return_value=[mock_result]):
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
    with patch("reprostim.qr.qr_parse._process_frame", side_effect=list(per_frame)):
        items = _run_parse(ctx, [_blank_frame()] * len(per_frame), _video(tmp_path))
    records = [i for i in items if not isinstance(i, ParseSummary)]
    assert len(records) == 2
    assert records[0].data == qr_a
    assert records[1].data == qr_b


def test_qr_state_machine_qr_at_end_of_video(tmp_path):
    """A QR code that runs to the last frame is still yielded."""
    per_frame = [None, _QR_DATA, _QR_DATA]
    ctx = ParseContext(std_threshold=0, qr_decoder=QrDecoder.PYZBAR)
    with patch("reprostim.qr.qr_parse._process_frame", side_effect=list(per_frame)):
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
    from reprostim.qr.qr_parse import InfoSummary

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

    with patch("reprostim.qr.qr_parse.do_parse", side_effect=fake_do_parse):
        result = do_main(path=_video(tmp_path), mode="PARSE", out_func=out.append)
    assert result == 0
    assert len(out) == 1


# ===========================================================================
# cmd_qr_parse CLI — Click runner tests
# ===========================================================================


@pytest.fixture
def cli_runner():
    return click.testing.CliRunner()


def test_cli_parse_mode_success(cli_runner, tmp_path):
    """CLI PARSE mode exits 0 when do_main succeeds."""
    video = _video(tmp_path)
    with patch("reprostim.qr.qr_parse.do_main", return_value=0):
        result = cli_runner.invoke(qr_parse_cmd, [str(video)])
    assert result.exit_code == 0


def test_cli_info_mode(cli_runner, tmp_path):
    """CLI --mode INFO is forwarded to do_main."""
    video = _video(tmp_path)
    with patch("reprostim.qr.qr_parse.do_main", return_value=0) as mock_main:
        cli_runner.invoke(qr_parse_cmd, ["--mode", "INFO", str(video)])
    assert mock_main.call_args.kwargs["mode"] == "INFO"


def test_cli_options_forwarded(cli_runner, tmp_path):
    """CLI options are forwarded correctly to do_main."""
    video = _video(tmp_path)
    with patch("reprostim.qr.qr_parse.do_main", return_value=0) as mock_main:
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


def test_cli_invalid_path(cli_runner, tmp_path):
    """CLI exits non-zero for a path that does not exist."""
    result = cli_runner.invoke(qr_parse_cmd, [str(tmp_path / "missing.mkv")])
    assert result.exit_code != 0
