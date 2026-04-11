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

import cv2
import numpy as np
import pytest

import reprostim.qr.qr_parse as qp_mod
from reprostim.qr.qr_parse import (
    Grayscale,
    ParseContext,
    ParseSummary,
    QrDecoder,
    VideoDecoder,
    _init_qrdet,
    _qrdet_filter,
    do_main,
    do_parse,
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
