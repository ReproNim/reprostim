# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for reprostim.bids.properties."""

from datetime import datetime

from reprostim.bids.properties import bids_properties_from_split_result
from reprostim.qr.split_video import SplitResult

# ===========================================================================
# bids_properties_from_split_result
# ===========================================================================


def _make_split_result() -> SplitResult:
    return SplitResult(
        success=True,
        input_path="/fake/input.mkv",
        output_path="/fake/output.mkv",
        buffer_before=5.0,
        buffer_after=5.0,
        buffer_duration=190.0,
        start_time=datetime(2024, 2, 2, 17, 30, 0),
        end_time=datetime(2024, 2, 2, 17, 33, 0),
        duration=180.0,
        video_width="1920",
        video_height="1080",
        video_frame_rate=30.0,
        video_size_mb=120.5,
        video_rate_mbpm=50.0,
        audio_sample_rate="48000",
        audio_bit_depth="16",
        audio_channel_count="2",
        audio_codec="aac",
        video_codec="h264",
        orig_buffer_start="17:25:00.000",
        orig_buffer_end="17:38:00.000",
        orig_buffer_offset=1500.0,
        orig_start="17:30:00.000",
        orig_end="17:33:00.000",
        orig_offset=1800.0,
        orig_device="TestDevice",
        orig_device_serial_number="SN-12345",
    )


def test_bids_properties_from_split_result_full_mapping():
    """All populated SplitResult fields map to correct BIDS keys."""
    sr = _make_split_result()
    data = bids_properties_from_split_result(sr)

    assert data["Device"] == "TestDevice"
    assert data["DeviceSerialNumber"] == "SN-12345"
    assert data["RecordingDuration"] == 190.0
    assert data["VideoCodec"] == "h264"
    assert data["VideoCodecRFC6381"] == "n/a"
    assert data["VideoFrameRate"] == 30.0
    assert data["ImageWidth"] == 1920
    assert data["ImageHeight"] == 1080
    assert data["AudioCodec"] == "aac"
    assert data["AudioCodecRFC6381"] == "n/a"
    assert data["AudioSampleRate"] == 48000.0
    assert data["AudioBitDepth"] == 16
    assert data["AudioChannelCount"] == 2


def test_bids_properties_from_split_result_na_fields_omitted():
    """Fields with value 'n/a' are omitted from BIDS output."""
    sr = SplitResult(
        duration=60.0,
        video_frame_rate=25.0,
        video_width="n/a",
        video_height="n/a",
        video_codec="n/a",
        audio_codec="n/a",
        audio_sample_rate="n/a",
        audio_bit_depth="n/a",
        audio_channel_count="n/a",
        orig_device="n/a",
        orig_device_serial_number="n/a",
    )
    data = bids_properties_from_split_result(sr)

    assert "Device" not in data
    assert "DeviceSerialNumber" not in data
    assert "ImageWidth" not in data
    assert "ImageHeight" not in data
    assert "VideoCodec" not in data
    assert "AudioCodec" not in data
    assert "AudioSampleRate" not in data
    assert "AudioBitDepth" not in data
    assert "AudioChannelCount" not in data
    assert "RecordingDuration" not in data
    assert data["VideoFrameRate"] == 25.0


def test_bids_properties_from_split_result_none_values_omitted():
    """Fields with None value are omitted from BIDS output."""
    sr = SplitResult(duration=None, video_frame_rate=None)
    data = bids_properties_from_split_result(sr)

    assert "RecordingDuration" not in data
    assert "VideoFrameRate" not in data


def test_bids_properties_from_split_result_numeric_types():
    """ImageWidth/ImageHeight are int, AudioSampleRate is float,
    AudioChannelCount is int."""
    sr = SplitResult(
        video_width="1280",
        video_height="720",
        audio_sample_rate="44100",
        audio_channel_count="1",
    )
    data = bids_properties_from_split_result(sr)

    assert isinstance(data["ImageWidth"], int) and data["ImageWidth"] == 1280
    assert isinstance(data["ImageHeight"], int) and data["ImageHeight"] == 720
    assert (
        isinstance(data["AudioSampleRate"], float)
        and data["AudioSampleRate"] == 44100.0
    )
    assert isinstance(data["AudioChannelCount"], int) and data["AudioChannelCount"] == 1


def test_bids_properties_from_split_result_video_codec_present_when_resolution_known():
    """VideoCodec and VideoCodecRFC6381 are included when video_codec is set."""
    sr = SplitResult(video_width="1920", video_height="1080", video_codec="h264")
    data = bids_properties_from_split_result(sr)
    assert data["VideoCodec"] == "h264"
    assert data["VideoCodecRFC6381"] == "n/a"


def test_bids_properties_from_split_result_video_codec_absent_when_na():
    """VideoCodec is omitted when video_codec is 'n/a' (no video stream)."""
    sr = SplitResult(video_width="n/a", video_height="n/a", video_codec="n/a")
    data = bids_properties_from_split_result(sr)
    assert "VideoCodec" not in data


def test_bids_properties_from_split_result_rfc6381_from_sidecar_metadata():
    """VideoCodecRFC6381 and AudioCodecRFC6381 are taken from sidecar_metadata."""
    sr = SplitResult(video_codec="h264", audio_codec="aac")
    data = bids_properties_from_split_result(
        sr,
        sidecar_metadata={
            "VideoCodecRFC6381": "avc1.640028",
            "AudioCodecRFC6381": "mp4a.40.2",
        },
    )
    assert data["VideoCodecRFC6381"] == "avc1.640028"
    assert data["AudioCodecRFC6381"] == "mp4a.40.2"


def test_bids_properties_from_split_result_rfc6381_def_to_na_wo_sidecar_metadata():
    """VideoCodecRFC6381 and AudioCodecRFC6381 default to 'n/a' when absent."""
    sr = SplitResult(video_codec="h264", audio_codec="aac")
    data = bids_properties_from_split_result(sr)
    assert data["VideoCodecRFC6381"] == "n/a"
    assert data["AudioCodecRFC6381"] == "n/a"


def test_bids_properties_from_split_result_bit_depth_pixel_format():
    """ImageBitDepth and ImagePixelFormat are written when present in
    sidecar_metadata."""
    sr = SplitResult(video_codec="h264")
    data = bids_properties_from_split_result(
        sr,
        sidecar_metadata={"ImageBitDepth": 10, "ImagePixelFormat": "yuv420p"},
    )
    assert data["ImageBitDepth"] == 10
    assert isinstance(data["ImageBitDepth"], int)
    assert data["ImagePixelFormat"] == "yuv420p"


def test_bids_properties_from_split_result_bit_depth_pixel_format_absent():
    """ImageBitDepth and ImagePixelFormat are omitted when absent from
    sidecar_metadata."""
    sr = SplitResult(video_codec="h264")
    data = bids_properties_from_split_result(sr)
    assert "ImageBitDepth" not in data
    assert "ImagePixelFormat" not in data


def test_bids_properties_from_split_result_video_frame_count_from_sidecar_metadata():
    """VideoFrameCount is written when present in sidecar_metadata."""
    sr = SplitResult(video_codec="h264")
    data = bids_properties_from_split_result(
        sr, sidecar_metadata={"VideoFrameCount": 270}
    )
    assert data["VideoFrameCount"] == 270
    assert isinstance(data["VideoFrameCount"], int)


def test_bids_properties_from_split_result_video_frame_count_absent_not_in_sidecar():
    """VideoFrameCount is omitted when absent from sidecar_metadata."""
    sr = SplitResult(video_codec="h264")
    data = bids_properties_from_split_result(sr)
    assert "VideoFrameCount" not in data


def test_bids_properties_from_split_result_no_raw_fields():
    """BIDS output contains no raw SplitResult field names."""
    sr = _make_split_result()
    data = bids_properties_from_split_result(sr)
    raw_keys = {
        "duration",
        "video_frame_rate",
        "video_width",
        "video_height",
        "video_codec",
        "audio_codec",
        "audio_sample_rate",
        "audio_bit_depth",
        "audio_channel_count",
        "orig_device",
        "orig_device_serial_number",
        "orig_start",
        "orig_end",
        "orig_buffer_start",
    }
    for key in raw_keys:
        assert key not in data, f"Raw field '{key}' should not appear in BIDS output"


def test_bids_properties_from_split_result_task_name_first_field():
    """TaskName from sidecar_metadata is output as the first field in BIDS JSON."""
    sr = _make_split_result()
    data = bids_properties_from_split_result(sr, sidecar_metadata={"TaskName": "rest"})
    assert data["TaskName"] == "rest"
    keys = list(data.keys())
    assert keys[0] == "TaskName", f"TaskName must be the first key, got: {keys}"


def test_bids_properties_from_split_result_task_name_absent_when_not_in_metadata():
    """TaskName is absent when sidecar_metadata does not contain it."""
    sr = _make_split_result()
    data = bids_properties_from_split_result(sr, sidecar_metadata={})
    assert "TaskName" not in data


def test_bids_properties_from_split_result_task_name_absent_when_metadata_is_none():
    """TaskName is absent when sidecar_metadata is None."""
    sr = _make_split_result()
    data = bids_properties_from_split_result(sr, sidecar_metadata=None)
    assert "TaskName" not in data


def test_bids_properties_from_split_result_task_name_first_before_device():
    """TaskName precedes Device in field order when both are present."""
    sr = _make_split_result()
    data = bids_properties_from_split_result(sr, sidecar_metadata={"TaskName": "faces"})
    keys = list(data.keys())
    assert "TaskName" in keys and "Device" in keys
    assert keys.index("TaskName") < keys.index("Device")
