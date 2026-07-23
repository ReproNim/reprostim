# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
Extraction of BIDS media-file properties (sidecar-JSON-key-keyed values)
from ffprobe results, split-video results, and in future from cached
VaRecord (videos.tsv) rows and file paths. The single place
bids-inject-sidecar, bids-inject, and split-video produce BIDS sidecar
properties from, instead of each reimplementing the
AudioInfo/VideoInfo/SplitResult/VaRecord -> BIDS-dict mapping
independently.

See .ai/bids/properties-spec.md for the full specification.
"""
import logging
from typing import Any, Dict, Optional

from reprostim.bids.media import BidsMediaProperty
from reprostim.capture.metadata import MetadataSessionBegin, find_metadata_by_class
from reprostim.video.audit import (
    AudioInfo,
    VaRecord,
    VideoInfo,
    get_audio_video_info_ffprobe,
    get_file_video_audit,
    parse_audio_sr,
)

# initialize the logger
logger = logging.getLogger(__name__)
logger.debug(f"name={__name__}")


def _set_prop(props: Dict[str, Any], key: BidsMediaProperty, value: Any) -> None:
    """Set ``props[key.value] = value``, skipping ``None`` values.

    Shared by the ``bids_properties_from_*`` functions in this module so a
    field that could not be determined is omitted from the result rather
    than written as ``"n/a"`` or ``None`` (BEP044 sidecar convention).
    """
    if value is not None:
        props[key.value] = value


def bids_properties_from_audio_video_info(
    audio: Optional[AudioInfo],
    video: Optional[VideoInfo],
    props: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Map ffprobe-derived stream info to BIDS media-file properties.

    Fields that cannot be determined (no matching stream, field absent from
    ffprobe output) are simply omitted from the result rather than written
    as ``"n/a"`` or ``None``, matching the BEP044 sidecar convention (see
    .ai/bids/media-spec.md).

    :param audio: Audio stream info from ``get_audio_video_info_ffprobe``,
        or ``None`` if the file has no audio stream.
    :type audio: Optional[AudioInfo]
    :param video: Video stream info from ``get_audio_video_info_ffprobe``,
        or ``None`` if the file has no video stream.
    :type video: Optional[~reprostim.video.audit.VideoInfo]
    :param props: Optional dict to populate/merge into instead of creating a
        fresh one — lets a caller accumulate properties from several
        ``bids_properties_from_*`` calls into one shared dict. Existing keys
        are overwritten by non-``None`` values from this call (like
        ``dict.update()``); when composing multiple sources, priority is
        controlled by call order, not by this parameter.
    :type props: Optional[Dict[str, Any]]
    :return: *props* (or a new dict if *props* was ``None``), with mappable
        properties set; only properties that could be determined are
        present.
    :rtype: Dict[str, Any]
    """
    if props is None:
        props = {}

    # RecordingDuration: prefer video's duration (the primary stream for
    # video/audiovideo files) over audio's when both are present.
    if video is not None and video.duration_sec is not None:
        _set_prop(props, BidsMediaProperty.RECORDING_DURATION, video.duration_sec)
    elif audio is not None:
        _set_prop(props, BidsMediaProperty.RECORDING_DURATION, audio.duration_sec)

    if audio is not None:
        _set_prop(props, BidsMediaProperty.AUDIO_CODEC, audio.codec)
        _set_prop(props, BidsMediaProperty.AUDIO_SAMPLE_RATE, audio.sample_rate)
        _set_prop(props, BidsMediaProperty.AUDIO_CHANNEL_COUNT, audio.channels)
        _set_prop(props, BidsMediaProperty.AUDIO_BIT_DEPTH, audio.bits_per_sample)
        _set_prop(props, BidsMediaProperty.AUDIO_CODEC_RFC6381, audio.codec_rfc6381)

    if video is not None:
        _set_prop(props, BidsMediaProperty.VIDEO_CODEC, video.codec)
        _set_prop(props, BidsMediaProperty.VIDEO_FRAME_RATE, video.fps)
        _set_prop(props, BidsMediaProperty.VIDEO_CODEC_RFC6381, video.codec_rfc6381)
        _set_prop(props, BidsMediaProperty.IMAGE_WIDTH, video.width)
        _set_prop(props, BidsMediaProperty.IMAGE_HEIGHT, video.height)
        _set_prop(props, BidsMediaProperty.IMAGE_PIXEL_FORMAT, video.pix_fmt)
        _set_prop(props, BidsMediaProperty.IMAGE_BIT_DEPTH, video.bit_depth)
        _set_prop(props, BidsMediaProperty.VIDEO_FRAME_COUNT, video.frame_count)

    return props


def bids_properties_from_ffprobe(
    path: str, props: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Run ``ffprobe`` on *path* and map the result to BIDS media-file
    properties.

    Convenience wrapper combining ``get_audio_video_info_ffprobe`` and
    :func:`bids_properties_from_audio_video_info`.

    :param path: Path to the audio/video file.
    :type path: str
    :param props: Optional dict to populate/merge into instead of creating a
        fresh one; see :func:`bids_properties_from_audio_video_info`.
    :type props: Optional[Dict[str, Any]]
    :return: *props* (or a new dict if *props* was ``None``); see
        :func:`bids_properties_from_audio_video_info`.
    :rtype: Dict[str, Any]
    """
    audio, video = get_audio_video_info_ffprobe(path)
    # logger.debug(f"audio: {audio}")
    # logger.debug(f"video: {video}")
    return bids_properties_from_audio_video_info(audio, video, props=props)


def bids_properties_from_split_result(
    sr, sidecar_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Convert a split-video result to a BEP044/BEP047 BIDS sidecar dict.

    Maps a video-splitting result's fields to BIDS metadata field names as
    defined in the common media file definitions
    (bids-standard/bids-specification PR #2367).

    *sr* is intentionally **untyped**: annotating it as
    ``reprostim.video.split.SplitResult`` would make this module import
    from ``video.split`` — but ``split.py`` is the caller of this
    function, so that import would be circular. *sr* is expected to expose
    the same attributes as ``SplitResult``: ``orig_device``,
    ``orig_device_serial_number``, ``buffer_duration``, ``video_codec``,
    ``video_frame_rate``, ``video_width``, ``video_height``, ``audio_codec``,
    ``audio_sample_rate``, ``audio_bit_depth``, ``audio_channel_count``.

    :param sr: Split-result-like object to convert (see note above).
    :param sidecar_metadata: Optional dict with extra BIDS fields to inject.
        Supports ``TaskName`` (written as the first field when present),
        ``VideoCodecRFC6381``, ``AudioCodecRFC6381``, ``ImageBitDepth``,
        ``ImagePixelFormat``, and ``VideoFrameCount`` (see
        :class:`BidsMediaProperty` for the field-name constants backing
        these keys).
    :type sidecar_metadata: Optional[Dict[str, Any]]
    :return: Dict with BIDS-compliant metadata field names.
    :rtype: Dict[str, Any]
    """
    result: Dict[str, Any] = {}

    if sidecar_metadata:
        task_name = sidecar_metadata.get("TaskName")
        if task_name:
            result["TaskName"] = task_name

    if sr.orig_device != "n/a":
        result["Device"] = sr.orig_device

    if sr.orig_device_serial_number != "n/a":
        result["DeviceSerialNumber"] = sr.orig_device_serial_number

    if sr.buffer_duration is not None:
        result[BidsMediaProperty.RECORDING_DURATION.value] = sr.buffer_duration

    if sr.video_codec != "n/a":
        result[BidsMediaProperty.VIDEO_CODEC.value] = sr.video_codec
        result[BidsMediaProperty.VIDEO_CODEC_RFC6381.value] = (
            sidecar_metadata or {}
        ).get(BidsMediaProperty.VIDEO_CODEC_RFC6381.value, "n/a")

    if sr.video_frame_rate is not None:
        result[BidsMediaProperty.VIDEO_FRAME_RATE.value] = sr.video_frame_rate

    if sr.video_width != "n/a":
        try:
            result[BidsMediaProperty.IMAGE_WIDTH.value] = int(sr.video_width)
        except (ValueError, TypeError):
            pass

    if sr.video_height != "n/a":
        try:
            result[BidsMediaProperty.IMAGE_HEIGHT.value] = int(sr.video_height)
        except (ValueError, TypeError):
            pass

    if sidecar_metadata:
        bit_depth = sidecar_metadata.get(BidsMediaProperty.IMAGE_BIT_DEPTH.value)
        if bit_depth is not None:
            try:
                result[BidsMediaProperty.IMAGE_BIT_DEPTH.value] = int(bit_depth)
            except (ValueError, TypeError):
                pass
        pix_fmt = sidecar_metadata.get(BidsMediaProperty.IMAGE_PIXEL_FORMAT.value)
        if pix_fmt:
            result[BidsMediaProperty.IMAGE_PIXEL_FORMAT.value] = pix_fmt
        frame_count = sidecar_metadata.get(BidsMediaProperty.VIDEO_FRAME_COUNT.value)
        if frame_count is not None:
            try:
                result[BidsMediaProperty.VIDEO_FRAME_COUNT.value] = int(frame_count)
            except (ValueError, TypeError):
                pass

    if sr.audio_codec != "n/a":
        result[BidsMediaProperty.AUDIO_CODEC.value] = sr.audio_codec
        result[BidsMediaProperty.AUDIO_CODEC_RFC6381.value] = (
            sidecar_metadata or {}
        ).get(BidsMediaProperty.AUDIO_CODEC_RFC6381.value, "n/a")

    if sr.audio_sample_rate != "n/a":
        try:
            result[BidsMediaProperty.AUDIO_SAMPLE_RATE.value] = float(
                sr.audio_sample_rate
            )
        except (ValueError, TypeError):
            pass

    if sr.audio_bit_depth != "n/a":
        try:
            result[BidsMediaProperty.AUDIO_BIT_DEPTH.value] = int(sr.audio_bit_depth)
        except (ValueError, TypeError):
            pass

    if sr.audio_channel_count != "n/a":
        try:
            result[BidsMediaProperty.AUDIO_CHANNEL_COUNT.value] = int(
                sr.audio_channel_count
            )
        except (ValueError, TypeError):
            pass

    return result


def bids_properties_from_video_audit(
    path: str,
    path_tsv: Optional[str] = None,
    props: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Look up a cached ``VaRecord`` for *path* in *path_tsv* (a
    ``videos.tsv`` produced by ``video-audit``) and map it to BIDS
    media-file properties.

    Wraps ``get_file_video_audit(path, path_tsv, cached=True,
    use_lock=False)``: prefers already-loaded, cached TSV data over
    reloading from disk, and skips the advisory file lock (dirty read) —
    appropriate for read-mostly batch tooling (e.g. ``bids-inject-sidecar``)
    rather than the ``video-audit`` writer itself. Falls back to auditing
    the file directly when *path* has no matching row in *path_tsv*, or
    *path_tsv* is not given/found — see
    :func:`reprostim.video.audit.get_file_video_audit`.

    Uses the ``VaRecord``'s ``duration``/``video_res_recorded``/
    ``video_fps_recorded``/``audio_sr`` fields (derived from the media
    stream itself via ffprobe/QR parsing), not the ``*_detected`` ones
    (derived from the psychopy display-capture log), since the sidecar
    should describe the file, not what was displayed. Fields absent or
    ``"n/a"`` in the ``VaRecord`` are omitted, matching every other
    ``bids_properties_from_*`` function in this module.

    ``VaRecord``/``videos.tsv`` has no ``Device``/``DeviceSerialNumber``
    columns yet, so those two are instead recovered the same way
    ``video.split`` does: by looking for a ``session_begin``
    REPROSTIM-METADATA-JSON entry in ``<path>.log`` (see
    :func:`reprostim.capture.metadata.find_metadata_by_class`) and reading its
    ``vDev``/``serial`` fields. Omitted if ``<path>.log`` doesn't exist, has
    no ``session_begin`` entry, or that entry lacks the field.

    ``VaRecord`` also has no codec column, so ``VideoCodec`` is set to
    ``"h264"`` whenever ``video_res_recorded`` is present (not ``"n/a"``),
    reflecting that ``reprostim-videocapture`` always encodes with
    ``-c:v libx264`` — matching ``SplitResult.video_codec``'s inference in
    ``bids_properties_from_split_result``.

    :param path: Path to the audio/video file.
    :type path: str
    :param path_tsv: Optional path to ``videos.tsv``.
    :type path_tsv: Optional[str]
    :param props: Optional dict to populate/merge into instead of creating a
        fresh one; see :func:`bids_properties_from_audio_video_info`.
    :type props: Optional[Dict[str, Any]]
    :return: *props* (or a new dict if *props* was ``None``); see
        :func:`bids_properties_from_audio_video_info`.
    :rtype: Dict[str, Any]
    """
    if props is None:
        props = {}

    va: VaRecord = get_file_video_audit(path, path_tsv, cached=True, use_lock=False)

    if va.duration and va.duration != "n/a":
        try:
            _set_prop(props, BidsMediaProperty.RECORDING_DURATION, float(va.duration))
        except (ValueError, TypeError):
            pass

    if va.video_res_recorded and va.video_res_recorded != "n/a":
        width_str, _, height_str = va.video_res_recorded.partition("x")
        try:
            width, height = int(width_str), int(height_str)
        except (ValueError, TypeError):
            pass
        else:
            _set_prop(props, BidsMediaProperty.IMAGE_WIDTH, width)
            _set_prop(props, BidsMediaProperty.IMAGE_HEIGHT, height)

        # VaRecord has no codec column; reprostim-videocapture always encodes
        # with -c:v libx264, so h264 is inferred whenever a resolution is
        # present, matching split.py's SplitResult.video_codec.
        _set_prop(props, BidsMediaProperty.VIDEO_CODEC, "h264")

    if va.video_fps_recorded and va.video_fps_recorded != "n/a":
        try:
            _set_prop(
                props,
                BidsMediaProperty.VIDEO_FRAME_RATE,
                float(va.video_fps_recorded),
            )
        except (ValueError, TypeError):
            pass

    audio = parse_audio_sr(va.audio_sr)

    if audio["audio_sample_rate"] != "n/a":
        try:
            _set_prop(
                props,
                BidsMediaProperty.AUDIO_SAMPLE_RATE,
                float(audio["audio_sample_rate"]),
            )
        except (ValueError, TypeError):
            pass

    if audio["audio_bit_depth"] != "n/a":
        # parse_audio_sr only ever sets this to a digit-string or "n/a"
        _set_prop(
            props, BidsMediaProperty.AUDIO_BIT_DEPTH, int(audio["audio_bit_depth"])
        )

    if audio["audio_channel_count"] != "n/a":
        # parse_audio_sr only ever sets this to a digit-string or "n/a"
        _set_prop(
            props,
            BidsMediaProperty.AUDIO_CHANNEL_COUNT,
            int(audio["audio_channel_count"]),
        )

    if audio["audio_codec"] != "n/a":
        _set_prop(props, BidsMediaProperty.AUDIO_CODEC, audio["audio_codec"])

    # Device/DeviceSerialNumber aren't part of VaRecord (see docstring); recover
    # them from the recording log's session_begin metadata, if present.
    sb = find_metadata_by_class(path + ".log", MetadataSessionBegin)
    if sb is not None:
        device = sb.vDev or "n/a"
        if device != "n/a":
            props["Device"] = device

        device_serial_number = sb.serial or "n/a"
        if device_serial_number != "n/a":
            props["DeviceSerialNumber"] = device_serial_number

    return props
