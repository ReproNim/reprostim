# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for reprostim.bids.properties."""

from datetime import datetime
from unittest.mock import patch

from reprostim.bids.properties import (
    bids_properties_from_audio_video_info,
    bids_properties_from_ffprobe,
    bids_properties_from_split_result,
    bids_properties_from_video_audit,
)
from reprostim.qr.split_video import SplitResult
from reprostim.qr.video_audit import AudioInfo, VaRecord, VideoInfo

# ===========================================================================
# bids_properties_from_audio_video_info
# ===========================================================================


def _make_audio_info(**overrides) -> AudioInfo:
    defaults = dict(
        codec="aac",
        sample_rate=48000,
        channels=2,
        bits_per_sample=16,
        codec_rfc6381="mp4a.40.2",
        duration_sec=12.5,
    )
    defaults.update(overrides)
    return AudioInfo(**defaults)


def _make_video_info(**overrides) -> VideoInfo:
    defaults = dict(
        codec="h264",
        fps=30.0,
        codec_rfc6381="avc1.640028",
        width=1920,
        height=1080,
        pix_fmt="yuv420p",
        bit_depth=8,
        duration_sec=12.0,
        frame_count=360,
    )
    defaults.update(overrides)
    return VideoInfo(**defaults)


def test_audio_video_info_both_present_full_mapping():
    """All AudioInfo/VideoInfo fields map to the correct BIDS keys."""
    audio = _make_audio_info()
    video = _make_video_info()
    data = bids_properties_from_audio_video_info(audio, video)

    assert data == {
        "RecordingDuration": 12.0,
        "AudioCodec": "aac",
        "AudioSampleRate": 48000,
        "AudioChannelCount": 2,
        "AudioBitDepth": 16,
        "AudioCodecRFC6381": "mp4a.40.2",
        "VideoCodec": "h264",
        "VideoFrameRate": 30.0,
        "VideoCodecRFC6381": "avc1.640028",
        "ImageWidth": 1920,
        "ImageHeight": 1080,
        "ImagePixelFormat": "yuv420p",
        "ImageBitDepth": 8,
        "VideoFrameCount": 360,
    }


def test_audio_video_info_recording_duration_prefers_video_when_both_set():
    """RecordingDuration comes from video.duration_sec when both are set."""
    audio = _make_audio_info(duration_sec=99.0)
    video = _make_video_info(duration_sec=12.0)
    data = bids_properties_from_audio_video_info(audio, video)
    assert data["RecordingDuration"] == 12.0


def test_audio_video_info_recording_duration_falls_back_to_audio():
    """RecordingDuration falls back to audio.duration_sec when video's is None."""
    audio = _make_audio_info(duration_sec=99.0)
    video = _make_video_info(duration_sec=None)
    data = bids_properties_from_audio_video_info(audio, video)
    assert data["RecordingDuration"] == 99.0


def test_audio_video_info_recording_duration_absent_when_neither_available():
    """RecordingDuration is absent when video has no duration and audio is None."""
    video = _make_video_info(duration_sec=None)
    data = bids_properties_from_audio_video_info(None, video)
    assert "RecordingDuration" not in data


def test_audio_video_info_audio_only():
    """audio-only: only audio-derived keys present, RecordingDuration from audio."""
    audio = _make_audio_info()
    data = bids_properties_from_audio_video_info(audio, None)
    assert data == {
        "RecordingDuration": 12.5,
        "AudioCodec": "aac",
        "AudioSampleRate": 48000,
        "AudioChannelCount": 2,
        "AudioBitDepth": 16,
        "AudioCodecRFC6381": "mp4a.40.2",
    }


def test_audio_video_info_video_only():
    """video-only: only video-derived keys present, RecordingDuration from video."""
    video = _make_video_info()
    data = bids_properties_from_audio_video_info(None, video)
    assert data == {
        "RecordingDuration": 12.0,
        "VideoCodec": "h264",
        "VideoFrameRate": 30.0,
        "VideoCodecRFC6381": "avc1.640028",
        "ImageWidth": 1920,
        "ImageHeight": 1080,
        "ImagePixelFormat": "yuv420p",
        "ImageBitDepth": 8,
        "VideoFrameCount": 360,
    }


def test_audio_video_info_both_none_returns_empty_dict():
    """audio=None, video=None -> {}."""
    assert bids_properties_from_audio_video_info(None, None) == {}


def test_audio_video_info_none_valued_audio_field_omitted():
    """A None-valued AudioInfo field is omitted, not written as None."""
    audio = _make_audio_info(codec=None, codec_rfc6381=None)
    data = bids_properties_from_audio_video_info(audio, None)
    assert "AudioCodec" not in data
    assert "AudioCodecRFC6381" not in data


def test_audio_video_info_none_valued_video_field_omitted():
    """A None-valued VideoInfo field is omitted, not written as None."""
    video = _make_video_info(pix_fmt=None, frame_count=None)
    data = bids_properties_from_audio_video_info(None, video)
    assert "ImagePixelFormat" not in data
    assert "VideoFrameCount" not in data


def test_audio_video_info_props_default_creates_fresh_dict_each_call():
    """props=None (default) returns a new dict on every call."""
    audio = _make_audio_info()
    r1 = bids_properties_from_audio_video_info(audio, None)
    r2 = bids_properties_from_audio_video_info(audio, None)
    assert r1 == r2
    assert r1 is not r2


def test_audio_video_info_props_shared_dict_mutated_and_returned():
    """props=<dict> is mutated in place and returned as the same object."""
    audio = _make_audio_info()
    shared: dict = {}
    result = bids_properties_from_audio_video_info(audio, None, props=shared)
    assert result is shared
    assert shared["AudioCodec"] == "aac"


def test_audio_video_info_props_overwrites_existing_key():
    """A pre-existing key in props is overwritten by this call's non-None value."""
    audio = _make_audio_info(codec="opus")
    shared = {"AudioCodec": "placeholder"}
    bids_properties_from_audio_video_info(audio, None, props=shared)
    assert shared["AudioCodec"] == "opus"


def test_audio_video_info_props_preserves_unrelated_key():
    """A pre-existing unrelated key in props survives untouched."""
    audio = _make_audio_info()
    shared = {"CustomField": "keep-me"}
    bids_properties_from_audio_video_info(audio, None, props=shared)
    assert shared["CustomField"] == "keep-me"
    assert shared["AudioCodec"] == "aac"


def test_audio_video_info_props_accumulates_across_two_calls():
    """Two separate calls (audio-only, then video-only) into the same shared
    props dict accumulate both sets of keys."""
    audio = _make_audio_info()
    video = _make_video_info()
    shared: dict = {}
    bids_properties_from_audio_video_info(audio, None, props=shared)
    bids_properties_from_audio_video_info(None, video, props=shared)
    assert shared["AudioCodec"] == "aac"
    assert shared["VideoCodec"] == "h264"


# ===========================================================================
# bids_properties_from_ffprobe
# ===========================================================================


def test_ffprobe_calls_get_audio_video_info_and_maps():
    """bids_properties_from_ffprobe wraps get_audio_video_info_ffprobe and
    bids_properties_from_audio_video_info."""
    audio = _make_audio_info()
    video = _make_video_info()
    with patch(
        "reprostim.bids.properties.get_audio_video_info_ffprobe",
        return_value=(audio, video),
    ) as mock_probe:
        data = bids_properties_from_ffprobe("fake.mkv")
    mock_probe.assert_called_once_with("fake.mkv")
    assert data == bids_properties_from_audio_video_info(audio, video)


def test_ffprobe_no_streams_returns_empty_dict():
    """A path ffprobe can't read (default-constructed AudioInfo/VideoInfo) -> {}."""
    with patch(
        "reprostim.bids.properties.get_audio_video_info_ffprobe",
        return_value=(AudioInfo(), VideoInfo()),
    ):
        data = bids_properties_from_ffprobe("/nonexistent.mkv")
    assert data == {}


def test_ffprobe_props_passthrough():
    """props is forwarded unchanged to bids_properties_from_audio_video_info."""
    audio = _make_audio_info()
    video = _make_video_info()
    shared = {"CustomField": "keep-me"}
    with patch(
        "reprostim.bids.properties.get_audio_video_info_ffprobe",
        return_value=(audio, video),
    ):
        result = bids_properties_from_ffprobe("fake.mkv", props=shared)
    assert result is shared
    assert shared["CustomField"] == "keep-me"
    assert shared["AudioCodec"] == "aac"


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


def test_bids_properties_from_split_result_invalid_video_width_omitted():
    """A non-numeric, non-'n/a' video_width is omitted, not raised."""
    sr = SplitResult(video_width="not-a-number", video_codec="h264")
    data = bids_properties_from_split_result(sr)
    assert "ImageWidth" not in data


def test_bids_properties_from_split_result_invalid_video_height_omitted():
    """A non-numeric, non-'n/a' video_height is omitted, not raised."""
    sr = SplitResult(video_height="not-a-number", video_codec="h264")
    data = bids_properties_from_split_result(sr)
    assert "ImageHeight" not in data


def test_bids_properties_from_split_result_invalid_audio_sample_rate_omitted():
    """A non-numeric, non-'n/a' audio_sample_rate is omitted, not raised."""
    sr = SplitResult(audio_sample_rate="not-a-number", audio_codec="aac")
    data = bids_properties_from_split_result(sr)
    assert "AudioSampleRate" not in data


def test_bids_properties_from_split_result_invalid_audio_bit_depth_omitted():
    """A non-numeric, non-'n/a' audio_bit_depth is omitted, not raised."""
    sr = SplitResult(audio_bit_depth="not-a-number", audio_codec="aac")
    data = bids_properties_from_split_result(sr)
    assert "AudioBitDepth" not in data


def test_bids_properties_from_split_result_invalid_audio_channel_count_omitted():
    """A non-numeric, non-'n/a' audio_channel_count is omitted, not raised."""
    sr = SplitResult(audio_channel_count="not-a-number", audio_codec="aac")
    data = bids_properties_from_split_result(sr)
    assert "AudioChannelCount" not in data


def test_bids_properties_from_split_result_inv_image_bit_depth_from_sidecar_omitted():
    """A non-numeric ImageBitDepth in sidecar_metadata is omitted, not raised."""
    sr = SplitResult(video_codec="h264")
    data = bids_properties_from_split_result(
        sr, sidecar_metadata={"ImageBitDepth": "not-a-number"}
    )
    assert "ImageBitDepth" not in data


def test_bids_properties_from_split_result_inv_frame_count_from_sidecar_omitted():
    """A non-numeric VideoFrameCount in sidecar_metadata is omitted, not raised."""
    sr = SplitResult(video_codec="h264")
    data = bids_properties_from_split_result(
        sr, sidecar_metadata={"VideoFrameCount": "not-a-number"}
    )
    assert "VideoFrameCount" not in data


# ===========================================================================
# bids_properties_from_video_audit
# ===========================================================================

_GET_FILE_VIDEO_AUDIT_PATCH = "reprostim.bids.properties.get_file_video_audit"


def _make_va_record(**overrides) -> VaRecord:
    defaults = dict(
        path="/data/a.mkv",
        duration="12.5",
        video_res_recorded="1920x1080",
        video_fps_recorded="30.0",
        audio_sr="48000Hz 16b 2ch aac",
    )
    defaults.update(overrides)
    return VaRecord(**defaults)


def test_video_audit_calls_get_file_video_audit_cached_no_lock():
    """cached=True, use_lock=False are hardcoded; path/path_tsv passed through."""
    va = _make_va_record()
    with patch(_GET_FILE_VIDEO_AUDIT_PATCH, return_value=va) as mock_gfva:
        bids_properties_from_video_audit("/data/a.mkv", "videos.tsv")
    mock_gfva.assert_called_once_with(
        "/data/a.mkv", "videos.tsv", cached=True, use_lock=False
    )


def test_video_audit_path_tsv_defaults_to_none():
    va = _make_va_record()
    with patch(_GET_FILE_VIDEO_AUDIT_PATCH, return_value=va) as mock_gfva:
        bids_properties_from_video_audit("/data/a.mkv")
    mock_gfva.assert_called_once_with("/data/a.mkv", None, cached=True, use_lock=False)


def test_video_audit_full_mapping():
    va = _make_va_record()
    with patch(_GET_FILE_VIDEO_AUDIT_PATCH, return_value=va):
        data = bids_properties_from_video_audit("/data/a.mkv", "videos.tsv")

    assert data == {
        "RecordingDuration": 12.5,
        "ImageWidth": 1920,
        "ImageHeight": 1080,
        "VideoFrameRate": 30.0,
        "AudioSampleRate": 48000.0,
        "AudioBitDepth": 16,
        "AudioChannelCount": 2,
        "AudioCodec": "aac",
    }
    assert isinstance(data["ImageWidth"], int)
    assert isinstance(data["ImageHeight"], int)
    assert isinstance(data["AudioBitDepth"], int)
    assert isinstance(data["AudioChannelCount"], int)


def test_video_audit_all_na_returns_empty_dict():
    va = _make_va_record(
        duration="n/a",
        video_res_recorded="n/a",
        video_fps_recorded="n/a",
        audio_sr="n/a",
    )
    with patch(_GET_FILE_VIDEO_AUDIT_PATCH, return_value=va):
        data = bids_properties_from_video_audit("/data/a.mkv")
    assert data == {}


def test_video_audit_duration_invalid_omitted():
    va = _make_va_record(duration="not-a-number")
    with patch(_GET_FILE_VIDEO_AUDIT_PATCH, return_value=va):
        data = bids_properties_from_video_audit("/data/a.mkv")
    assert "RecordingDuration" not in data


def test_video_audit_resolution_invalid_omits_both_dimensions():
    va = _make_va_record(video_res_recorded="bogus")
    with patch(_GET_FILE_VIDEO_AUDIT_PATCH, return_value=va):
        data = bids_properties_from_video_audit("/data/a.mkv")
    assert "ImageWidth" not in data
    assert "ImageHeight" not in data


def test_video_audit_fps_invalid_omitted():
    va = _make_va_record(video_fps_recorded="not-a-number")
    with patch(_GET_FILE_VIDEO_AUDIT_PATCH, return_value=va):
        data = bids_properties_from_video_audit("/data/a.mkv")
    assert "VideoFrameRate" not in data


def test_video_audit_audio_sample_rate_only():
    """audio_sr with only a sample rate: sample rate set, bit depth defaults
    to 16 per parse_audio_sr, channel count/codec omitted."""
    va = _make_va_record(audio_sr="44100Hz")
    with patch(_GET_FILE_VIDEO_AUDIT_PATCH, return_value=va):
        data = bids_properties_from_video_audit("/data/a.mkv")
    assert data["AudioSampleRate"] == 44100.0
    assert data["AudioBitDepth"] == 16
    assert "AudioChannelCount" not in data
    assert "AudioCodec" not in data


def test_video_audit_props_default_creates_fresh_dict_each_call():
    va = _make_va_record()
    with patch(_GET_FILE_VIDEO_AUDIT_PATCH, return_value=va):
        first = bids_properties_from_video_audit("/data/a.mkv")
        second = bids_properties_from_video_audit("/data/a.mkv")
    assert first is not second


def test_video_audit_audio_sample_rate_invalid_omitted():
    """parse_audio_sr doesn't digit-validate the Hz token, so a malformed
    audio_sr can yield a non-numeric audio_sample_rate; must be omitted, not
    raised."""
    va = _make_va_record(audio_sr="abcHz")
    with patch(_GET_FILE_VIDEO_AUDIT_PATCH, return_value=va):
        data = bids_properties_from_video_audit("/data/a.mkv")
    assert "AudioSampleRate" not in data


def test_video_audit_props_shared_dict_mutated_and_returned():
    va = _make_va_record()
    shared = {"CustomField": "keep-me"}
    with patch(_GET_FILE_VIDEO_AUDIT_PATCH, return_value=va):
        result = bids_properties_from_video_audit("/data/a.mkv", props=shared)
    assert result is shared
    assert shared["CustomField"] == "keep-me"
    assert shared["AudioCodec"] == "aac"
