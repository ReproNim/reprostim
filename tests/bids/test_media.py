# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for reprostim.bids.media."""

from reprostim.bids.media import (
    AudioFormat,
    BidsMediaCodec,
    BidsMediaErrorCode,
    BidsMediaInfo,
    BidsMediaInfoError,
    BidsMediaProperty,
    BidsMediaType,
    ImageFormat,
    VideoFormat,
    _format_from_extension,
    _media_type_from_format,
    parse_bids_media_info,
)

# ===========================================================================
# BidsMediaType
# ===========================================================================


def test_bids_media_type_members():
    assert BidsMediaType.AUDIO.value == "audio"
    assert BidsMediaType.AUDIOVIDEO.value == "audiovideo"
    assert BidsMediaType.IMAGE.value == "image"
    assert BidsMediaType.VIDEO.value == "video"
    assert len(BidsMediaType) == 4


# ===========================================================================
# AudioFormat / ImageFormat / VideoFormat
# ===========================================================================


def test_audio_format_members():
    assert {m.value for m in AudioFormat} == {"wav", "flac", "mp3", "aac", "ogg"}


def test_image_format_members():
    assert {m.value for m in ImageFormat} == {
        "jpg",
        "png",
        "svg",
        "webp",
        "tif",
        "tiff",
    }


def test_video_format_members():
    assert {m.value for m in VideoFormat} == {"mp4", "avi", "mkv", "webm"}


def test_format_enum_values_have_no_leading_dot():
    for member in list(AudioFormat) + list(ImageFormat) + list(VideoFormat):
        assert not member.value.startswith(".")


# ===========================================================================
# BidsMediaCodec
# ===========================================================================


def test_bids_media_codec_members_and_values():
    assert BidsMediaCodec.H264.value == "h264"
    assert BidsMediaCodec.HEVC.value == "hevc"
    assert BidsMediaCodec.VP9.value == "vp9"
    assert BidsMediaCodec.AV1.value == "av1"
    assert BidsMediaCodec.AAC.value == "aac"
    assert BidsMediaCodec.MP3.value == "mp3"
    assert BidsMediaCodec.OPUS.value == "opus"
    assert BidsMediaCodec.FLAC.value == "flac"
    assert BidsMediaCodec.PCM_S16LE.value == "pcm_s16le"
    assert len(BidsMediaCodec) == 9


def test_bids_media_codec_rfc6381():
    assert BidsMediaCodec.H264.rfc6381 == "avc1.640028"
    assert BidsMediaCodec.AAC.rfc6381 == "mp4a.40.2"
    assert BidsMediaCodec.PCM_S16LE.rfc6381 is None


def test_bids_media_codec_category():
    assert BidsMediaCodec.H264.category == BidsMediaType.VIDEO
    assert BidsMediaCodec.AAC.category == BidsMediaType.AUDIO


def test_bids_media_codec_for_category_video():
    video_codecs = {c.value for c in BidsMediaCodec.for_category(BidsMediaType.VIDEO)}
    assert video_codecs == {"h264", "hevc", "vp9", "av1"}


def test_bids_media_codec_for_category_audio():
    audio_codecs = {c.value for c in BidsMediaCodec.for_category(BidsMediaType.AUDIO)}
    assert audio_codecs == {"aac", "mp3", "opus", "flac", "pcm_s16le"}


def test_bids_media_codec_for_category_image_is_empty():
    """No codec applies to IMAGE (codecs are audio/video-only in this table)."""
    assert BidsMediaCodec.for_category(BidsMediaType.IMAGE) == []


def test_bids_media_codec_equals_plain_string():
    assert BidsMediaCodec.H264 == "h264"


# ===========================================================================
# BidsMediaErrorCode
# ===========================================================================


def test_bids_media_error_code_members():
    assert BidsMediaErrorCode.INVALID_PATH.value == "invalid_path"
    assert BidsMediaErrorCode.UNKNOWN_EXTENSION.value == "unknown_extension"
    assert BidsMediaErrorCode.UNKNOWN_MEDIA_TYPE.value == "unknown_media_type"
    assert BidsMediaErrorCode.MEDIA_TYPE_MISMATCH.value == "media_type_mismatch"


# ===========================================================================
# BidsMediaProperty
# ===========================================================================


def test_bids_media_property_count_and_values():
    assert len(BidsMediaProperty) == 14
    assert BidsMediaProperty.RECORDING_DURATION.value == "RecordingDuration"
    assert BidsMediaProperty.AUDIO_CODEC.value == "AudioCodec"
    assert BidsMediaProperty.AUDIO_SAMPLE_RATE.value == "AudioSampleRate"
    assert BidsMediaProperty.AUDIO_CHANNEL_COUNT.value == "AudioChannelCount"
    assert BidsMediaProperty.AUDIO_BIT_DEPTH.value == "AudioBitDepth"
    assert BidsMediaProperty.AUDIO_CODEC_RFC6381.value == "AudioCodecRFC6381"
    assert BidsMediaProperty.IMAGE_WIDTH.value == "ImageWidth"
    assert BidsMediaProperty.IMAGE_HEIGHT.value == "ImageHeight"
    assert BidsMediaProperty.IMAGE_PIXEL_FORMAT.value == "ImagePixelFormat"
    assert BidsMediaProperty.IMAGE_BIT_DEPTH.value == "ImageBitDepth"
    assert BidsMediaProperty.VIDEO_CODEC.value == "VideoCodec"
    assert BidsMediaProperty.VIDEO_FRAME_RATE.value == "VideoFrameRate"
    assert BidsMediaProperty.VIDEO_FRAME_COUNT.value == "VideoFrameCount"
    assert BidsMediaProperty.VIDEO_CODEC_RFC6381.value == "VideoCodecRFC6381"


def test_bids_media_property_equals_plain_string():
    assert BidsMediaProperty.AUDIO_CODEC == "AudioCodec"


def test_bids_media_property_categories():
    assert BidsMediaProperty.RECORDING_DURATION.categories == frozenset(
        {BidsMediaType.AUDIO, BidsMediaType.VIDEO, BidsMediaType.AUDIOVIDEO}
    )
    assert BidsMediaProperty.IMAGE_WIDTH.categories == frozenset(
        {BidsMediaType.VIDEO, BidsMediaType.AUDIOVIDEO, BidsMediaType.IMAGE}
    )


def test_bids_media_property_for_category_audio():
    names = {p.value for p in BidsMediaProperty.for_category(BidsMediaType.AUDIO)}
    assert names == {
        "RecordingDuration",
        "AudioCodec",
        "AudioSampleRate",
        "AudioChannelCount",
        "AudioBitDepth",
        "AudioCodecRFC6381",
    }


def test_bids_media_property_for_category_video():
    names = {p.value for p in BidsMediaProperty.for_category(BidsMediaType.VIDEO)}
    assert names == {
        "RecordingDuration",
        "ImageWidth",
        "ImageHeight",
        "ImagePixelFormat",
        "ImageBitDepth",
        "VideoCodec",
        "VideoFrameRate",
        "VideoFrameCount",
        "VideoCodecRFC6381",
    }


def test_bids_media_property_for_category_image():
    names = {p.value for p in BidsMediaProperty.for_category(BidsMediaType.IMAGE)}
    assert names == {
        "ImageWidth",
        "ImageHeight",
        "ImagePixelFormat",
        "ImageBitDepth",
    }


def test_bids_media_property_for_category_audiovideo():
    names = {p.value for p in BidsMediaProperty.for_category(BidsMediaType.AUDIOVIDEO)}
    # Every property except the four IMAGE-only-with-video ones is shared;
    # in fact IMAGE_* also include AUDIOVIDEO, so AUDIOVIDEO gets all 14.
    assert names == {p.value for p in BidsMediaProperty}


def test_bids_media_property_usable_as_json_dumps_key():
    """BidsMediaProperty members drop directly into json.dumps as plain
    string keys, with no .value step needed."""
    import json

    payload = json.dumps({BidsMediaProperty.AUDIO_CODEC: "aac"})
    assert payload == '{"AudioCodec": "aac"}'


# ===========================================================================
# BidsMediaInfoError
# ===========================================================================


def test_bids_media_info_error_construction():
    err = BidsMediaInfoError(
        code=BidsMediaErrorCode.UNKNOWN_EXTENSION, message="bad extension"
    )
    assert err.code == BidsMediaErrorCode.UNKNOWN_EXTENSION
    assert err.message == "bad extension"


# ===========================================================================
# BidsMediaInfo
# ===========================================================================


def test_bids_media_info_defaults():
    info = BidsMediaInfo(path="foo.mkv")
    assert info.path == "foo.mkv"
    assert info.media_type is None
    assert info.format is None
    assert info.errors == []
    assert info.valid is True


def test_bids_media_info_valid_false_when_errors_present():
    info = BidsMediaInfo(
        path="foo.mkv",
        errors=[
            BidsMediaInfoError(code=BidsMediaErrorCode.INVALID_PATH, message="bad")
        ],
    )
    assert info.valid is False


def test_bids_media_info_valid_is_derived_not_stored():
    """valid flips back to True if errors is cleared -- it's a computed
    property, never a stale stored field."""
    info = BidsMediaInfo(
        path="foo.mkv",
        errors=[
            BidsMediaInfoError(code=BidsMediaErrorCode.INVALID_PATH, message="bad")
        ],
    )
    assert info.valid is False
    info.errors = []
    assert info.valid is True


def test_bids_media_info_multiple_errors():
    info = BidsMediaInfo(
        path="foo.xyz",
        errors=[
            BidsMediaInfoError(code=BidsMediaErrorCode.UNKNOWN_EXTENSION, message="a"),
            BidsMediaInfoError(code=BidsMediaErrorCode.UNKNOWN_MEDIA_TYPE, message="b"),
        ],
    )
    assert len(info.errors) == 2
    assert info.valid is False


def test_bids_media_info_format_accepts_each_format_type():
    """format: Optional[Union[AudioFormat, VideoFormat, ImageFormat]] accepts
    a member from any of the three format enums."""
    assert BidsMediaInfo(path="a.wav", format=AudioFormat.WAV).format == AudioFormat.WAV
    assert BidsMediaInfo(path="a.mkv", format=VideoFormat.MKV).format == VideoFormat.MKV
    assert BidsMediaInfo(path="a.png", format=ImageFormat.PNG).format == ImageFormat.PNG


def test_bids_media_info_round_trip_model_dump_and_validate():
    """BidsMediaInfo (with nested BidsMediaInfoError) survives a
    model_dump()/model_validate() round trip unchanged."""
    original = BidsMediaInfo(
        path="sub-01_task-rest_recording-reprostim_video.mkv",
        media_type=BidsMediaType.VIDEO,
        format=VideoFormat.MKV,
        errors=[
            BidsMediaInfoError(code=BidsMediaErrorCode.UNKNOWN_EXTENSION, message="x")
        ],
    )
    restored = BidsMediaInfo.model_validate(original.model_dump())
    assert restored == original
    assert restored.valid is False


# ===========================================================================
# _format_from_extension (private)
# ===========================================================================


def test_format_from_extension_audio():
    assert _format_from_extension("wav") == AudioFormat.WAV
    assert _format_from_extension("mp3") == AudioFormat.MP3


def test_format_from_extension_video():
    assert _format_from_extension("mkv") == VideoFormat.MKV
    assert _format_from_extension("mp4") == VideoFormat.MP4


def test_format_from_extension_image():
    assert _format_from_extension("png") == ImageFormat.PNG
    assert _format_from_extension("tiff") == ImageFormat.TIFF


def test_format_from_extension_unknown_returns_none():
    assert _format_from_extension("xyz") is None


def test_format_from_extension_uppercase_not_matched():
    """The helper expects an already-lowercased extension; uppercase input
    is not matched (case-normalization is the caller's job)."""
    assert _format_from_extension("WAV") is None


# ===========================================================================
# _media_type_from_format (private)
# ===========================================================================


def test_media_type_from_format_audio():
    assert _media_type_from_format(AudioFormat.MP3) == BidsMediaType.AUDIO


def test_media_type_from_format_image():
    assert _media_type_from_format(ImageFormat.PNG) == BidsMediaType.IMAGE


def test_media_type_from_format_video():
    """VideoFormat is ambiguous (VIDEO vs AUDIOVIDEO) -- VIDEO is the
    conservative default."""
    assert _media_type_from_format(VideoFormat.MKV) == BidsMediaType.VIDEO


def test_media_type_from_format_none():
    assert _media_type_from_format(None) is None


# ===========================================================================
# parse_bids_media_info
# ===========================================================================


def test_parse_valid_video_suffix_and_extension():
    info = parse_bids_media_info("sub-01_task-rest_recording-reprostim_video.mkv")
    assert info.valid is True
    assert info.media_type == BidsMediaType.VIDEO
    assert info.format == VideoFormat.MKV
    assert info.errors == []


def test_parse_valid_audio_suffix_and_extension():
    info = parse_bids_media_info("sub-01_task-rest_recording-reprostim_audio.wav")
    assert info.valid is True
    assert info.media_type == BidsMediaType.AUDIO
    assert info.format == AudioFormat.WAV


def test_parse_valid_audiovideo_suffix_and_extension():
    info = parse_bids_media_info("sub-01_task-rest_recording-reprostim_audiovideo.mp4")
    assert info.valid is True
    assert info.media_type == BidsMediaType.AUDIOVIDEO
    assert info.format == VideoFormat.MP4


def test_parse_valid_image_suffix_and_extension():
    info = parse_bids_media_info("sub-01_task-rest_recording-reprostim_image.png")
    assert info.valid is True
    assert info.media_type == BidsMediaType.IMAGE
    assert info.format == ImageFormat.PNG


def test_parse_no_valid_suffix_falls_back_to_video_extension():
    info = parse_bids_media_info("sub-01_task-rest_myrecording.mkv")
    assert info.valid is False
    assert info.media_type == BidsMediaType.VIDEO
    assert info.format == VideoFormat.MKV
    assert len(info.errors) == 1
    assert info.errors[0].code == BidsMediaErrorCode.UNKNOWN_MEDIA_TYPE


def test_parse_no_valid_suffix_falls_back_to_audio_extension():
    info = parse_bids_media_info("sub-01_task-rest_myrecording.wav")
    assert info.valid is False
    assert info.media_type == BidsMediaType.AUDIO
    assert info.format == AudioFormat.WAV
    assert info.errors[0].code == BidsMediaErrorCode.UNKNOWN_MEDIA_TYPE


def test_parse_no_valid_suffix_falls_back_to_image_extension():
    info = parse_bids_media_info("sub-01_task-rest_myrecording.png")
    assert info.valid is False
    assert info.media_type == BidsMediaType.IMAGE
    assert info.format == ImageFormat.PNG
    assert info.errors[0].code == BidsMediaErrorCode.UNKNOWN_MEDIA_TYPE


def test_parse_no_valid_suffix_and_unknown_extension():
    info = parse_bids_media_info("sub-01_task-rest_myrecording.xyz")
    assert info.valid is False
    assert info.media_type is None
    assert info.format is None
    codes = {e.code for e in info.errors}
    assert codes == {
        BidsMediaErrorCode.UNKNOWN_EXTENSION,
        BidsMediaErrorCode.UNKNOWN_MEDIA_TYPE,
    }


def test_parse_valid_suffix_unknown_extension():
    """Valid suffix resolves media_type; format stays None with only an
    UNKNOWN_EXTENSION error."""
    info = parse_bids_media_info("sub-01_task-rest_recording-reprostim_video.xyz")
    assert info.valid is False
    assert info.media_type == BidsMediaType.VIDEO
    assert info.format is None
    assert len(info.errors) == 1
    assert info.errors[0].code == BidsMediaErrorCode.UNKNOWN_EXTENSION


def test_parse_no_extension_at_all_is_invalid_path():
    info = parse_bids_media_info("novalidname")
    assert info.valid is False
    assert info.media_type is None
    assert info.format is None
    assert len(info.errors) == 1
    assert info.errors[0].code == BidsMediaErrorCode.INVALID_PATH


def test_parse_empty_string_is_invalid_path():
    info = parse_bids_media_info("")
    assert info.valid is False
    assert info.errors[0].code == BidsMediaErrorCode.INVALID_PATH


def test_parse_case_insensitive_suffix_and_extension():
    info = parse_bids_media_info("/a/b/sub-01_VIDEO.MP4")
    assert info.valid is True
    assert info.media_type == BidsMediaType.VIDEO
    assert info.format == VideoFormat.MP4


def test_parse_full_path_with_directories():
    info = parse_bids_media_info(
        "/data/bids/sub-01/func/sub-01_task-rest_recording-reprostim_video.mkv"
    )
    assert info.valid is True
    assert info.media_type == BidsMediaType.VIDEO
    assert info.path == (
        "/data/bids/sub-01/func/sub-01_task-rest_recording-reprostim_video.mkv"
    )


def test_parse_no_underscore_in_stem_still_checks_whole_stem_as_suffix():
    """A stem with no underscore at all is itself the candidate suffix
    token."""
    info = parse_bids_media_info("video.mkv")
    assert info.media_type == BidsMediaType.VIDEO
    assert info.valid is True
