# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Unit tests for ``reprostim.video.media_info``.

Covers: ``check_ffprobe``, ``parse_audio_sr``, ``audio_codec_to_rfc6381``,
``video_codec_to_rfc6381``, and ``get_audio_video_info_ffprobe``.
"""

import json
import pathlib
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from reprostim.video.media_info import (
    audio_codec_to_rfc6381,
    check_ffprobe,
    get_audio_video_info_ffprobe,
    parse_audio_sr,
    video_codec_to_rfc6381,
)

_DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "video"

# ===========================================================================
# parse_audio_sr
# ===========================================================================


def test_parse_audio_sr_full_string():
    """Full audio info string parses all four fields correctly."""
    result = parse_audio_sr("48000Hz 16b 2ch aac")
    assert result["audio_sample_rate"] == "48000"
    assert result["audio_bit_depth"] == "16"
    assert result["audio_channel_count"] == "2"
    assert result["audio_codec"] == "aac"


def test_parse_audio_sr_missing_bit_depth_defaults_to_16():
    """String without explicit bit depth defaults audio_bit_depth to '16'."""
    result = parse_audio_sr("48000Hz 2ch aac")
    assert result["audio_sample_rate"] == "48000"
    assert result["audio_bit_depth"] == "16"
    assert result["audio_channel_count"] == "2"
    assert result["audio_codec"] == "aac"


def test_parse_audio_sr_none_returns_na():
    """None input returns all n/a fields."""
    result = parse_audio_sr(None)
    assert all(v == "n/a" for v in result.values())


def test_parse_audio_sr_na_string_returns_na():
    """'n/a' string returns all n/a fields."""
    result = parse_audio_sr("n/a")
    assert all(v == "n/a" for v in result.values())


def test_parse_audio_sr_empty_string_returns_na():
    """Empty string returns all n/a fields."""
    result = parse_audio_sr("")
    assert all(v == "n/a" for v in result.values())


def test_parse_audio_sr_sample_rate_only():
    """String with only sample rate populates that field; others are n/a or default."""
    result = parse_audio_sr("44100Hz")
    assert result["audio_sample_rate"] == "44100"
    assert result["audio_bit_depth"] == "16"  # hardcoded default


# ===========================================================================
# check_ffprobe
# ===========================================================================


def test_check_ffprobe_available():
    with patch(
        "reprostim.video.media_info.subprocess.run",
        return_value=MagicMock(returncode=0),
    ):
        assert check_ffprobe() is True


def test_check_ffprobe_not_found():
    with patch(
        "reprostim.video.media_info.subprocess.run", side_effect=FileNotFoundError
    ):
        assert check_ffprobe() is False


def test_check_ffprobe_nonzero_exit_returns_false():
    with patch(
        "reprostim.video.media_info.subprocess.run",
        return_value=MagicMock(returncode=1, args=["ffprobe", "-version"]),
    ):
        assert check_ffprobe() is False


def test_check_ffprobe_not_found_reraise_true_raises():
    with patch(
        "reprostim.video.media_info.subprocess.run", side_effect=FileNotFoundError
    ):
        with pytest.raises(FileNotFoundError):
            check_ffprobe(reraise=True)


def test_check_ffprobe_nonzero_exit_reraise_true_raises():
    with patch(
        "reprostim.video.media_info.subprocess.run",
        return_value=MagicMock(returncode=1, args=["ffprobe", "-version"]),
    ):
        with pytest.raises(subprocess.CalledProcessError):
            check_ffprobe(reraise=True)


def test_check_ffprobe_available_reraise_true_still_returns_true():
    """reraise only affects the failure path; success is unaffected."""
    with patch(
        "reprostim.video.media_info.subprocess.run",
        return_value=MagicMock(returncode=0),
    ):
        assert check_ffprobe(reraise=True) is True


# ===========================================================================
# audio_codec_to_rfc6381 / video_codec_to_rfc6381
# ===========================================================================


def test_audio_codec_to_rfc6381_aac_lc():
    assert audio_codec_to_rfc6381("aac", "LC") == "mp4a.40.2"


def test_audio_codec_to_rfc6381_aac_he():
    assert audio_codec_to_rfc6381("aac", "HE-AAC") == "mp4a.40.5"


def test_audio_codec_to_rfc6381_aac_unknown_profile():
    assert audio_codec_to_rfc6381("aac", None) == "mp4a.40.2"


def test_audio_codec_to_rfc6381_mp3():
    assert audio_codec_to_rfc6381("mp3", None) == "mp4a.69"


def test_audio_codec_to_rfc6381_opus():
    assert audio_codec_to_rfc6381("opus", None) == "opus"


def test_audio_codec_to_rfc6381_unknown():
    assert audio_codec_to_rfc6381("pcm_s16le", None) is None


def test_video_codec_to_rfc6381_h264_high():
    assert video_codec_to_rfc6381("h264", "High", 42) == "avc1.640002A".replace(
        "0002A", "002A"
    )
    assert video_codec_to_rfc6381("h264", "High", 42) == "avc1.64002A"


def test_video_codec_to_rfc6381_h264_baseline():
    assert video_codec_to_rfc6381("h264", "Baseline", 30) == "avc1.42001E"


def test_video_codec_to_rfc6381_h264_no_level():
    result = video_codec_to_rfc6381("h264", "Main", None)
    assert result == "avc1.4D0000"


def test_video_codec_to_rfc6381_unknown():
    assert video_codec_to_rfc6381("vp9", None, None) is None


# ===========================================================================
# get_audio_video_info_ffprobe
# ===========================================================================

_FULL_FFPROBE_OUTPUT = (_DATA_DIR / "ffprobe_h264_aac.json").read_text()


def test_get_audio_video_info_ffprobe_audio_fields():
    mock_result = MagicMock(stdout=_FULL_FFPROBE_OUTPUT, returncode=0)
    with patch("reprostim.video.media_info.subprocess.run", return_value=mock_result):
        ai, vi = get_audio_video_info_ffprobe("/fake/test.mkv")
    assert ai.codec == "aac"
    assert ai.codec_long == "AAC (Advanced Audio Coding)"
    assert ai.profile == "LC"
    assert ai.sample_rate == 48000
    assert ai.channels == 2
    assert ai.bits_per_sample is None  # 0 is treated as absent
    assert ai.codec_rfc6381 == "mp4a.40.2"
    assert abs(ai.duration_sec - (2 * 3600 + 50 * 60 + 16.420)) < 0.01
    assert ai.start_time == 0.0
    assert ai.tag_str == "[0][0][0][0]"


def test_get_audio_video_info_ffprobe_video_fields():
    mock_result = MagicMock(stdout=_FULL_FFPROBE_OUTPUT, returncode=0)
    with patch("reprostim.video.media_info.subprocess.run", return_value=mock_result):
        ai, vi = get_audio_video_info_ffprobe("/fake/test.mkv")
    assert vi.codec == "h264"
    assert vi.codec_long == "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10"
    assert vi.profile == "High"
    assert vi.level == 42
    assert vi.width == 1920
    assert vi.height == 1080
    assert vi.pix_fmt == "yuv420p"
    assert vi.bit_depth == 8
    assert abs(vi.fps - 60.0) < 0.01
    assert vi.codec_rfc6381 == "avc1.64002A"
    assert abs(vi.duration_sec - (2 * 3600 + 50 * 60 + 16.438)) < 0.01
    assert vi.start_time == pytest.approx(0.021)
    assert vi.tag_str == "[0][0][0][0]"


def test_get_audio_video_info_ffprobe_duration_from_stream_field():
    output = json.dumps(
        {
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "48000",
                    "channels": 1,
                    "duration": "30.5",
                }
            ]
        }
    )
    mock_result = MagicMock(stdout=output, returncode=0)
    with patch("reprostim.video.media_info.subprocess.run", return_value=mock_result):
        ai, vi = get_audio_video_info_ffprobe("/fake/test.mkv")
    assert abs(ai.duration_sec - 30.5) < 0.01
    assert vi.codec is None


def test_get_audio_video_info_ffprobe_no_audio_streams():
    output = json.dumps(
        {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "profile": "High",
                    "level": 40,
                    "width": 1280,
                    "height": 720,
                    "avg_frame_rate": "30/1",
                }
            ]
        }
    )
    mock_result = MagicMock(stdout=output, returncode=0)
    with patch("reprostim.video.media_info.subprocess.run", return_value=mock_result):
        ai, vi = get_audio_video_info_ffprobe("/fake/test.mkv")
    assert ai.codec is None
    assert vi.codec == "h264"


def test_get_audio_video_info_ffprobe_not_found():
    with patch(
        "reprostim.video.media_info.subprocess.run", side_effect=FileNotFoundError
    ):
        ai, vi = get_audio_video_info_ffprobe("/fake/test.mkv")
    assert ai.codec is None
    assert vi.codec is None


def test_get_audio_video_info_ffprobe_called_process_error():
    err = subprocess.CalledProcessError(1, "ffprobe", output="", stderr="error")
    with patch("reprostim.video.media_info.subprocess.run", side_effect=err):
        ai, vi = get_audio_video_info_ffprobe("/fake/test.mkv")
    assert ai.codec is None
    assert vi.codec is None
