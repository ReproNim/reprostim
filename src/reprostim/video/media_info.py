# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
API to extract audio/video stream information (codec, resolution, duration,
sample rate, etc.) from a media file. Currently backed by `ffprobe`, but
deliberately named/organized so the extraction mechanism can change without
forcing callers to update their imports.
"""

import json
import logging
import subprocess
from typing import Optional, Tuple

from pydantic import BaseModel

# initialize the logger
# Note: all logs out to stderr
logger = logging.getLogger(__name__)
logger.debug(f"name={__name__}")


class AudioInfo(BaseModel):
    """Audio stream information extracted from the video file with ffprobe."""

    bits_per_sample: Optional[int] = None  # Bits per sample
    channels: Optional[int] = None  # Number of audio channels
    codec: Optional[str] = None  # Audio codec used
    codec_long: Optional[str] = None  # Audio codec detailed name
    codec_rfc6381: Optional[str] = None  # Audio codec in RFC 6381 format
    duration_sec: Optional[float] = None  # Duration in seconds
    profile: Optional[str] = None  # Audio codec profile (e.g., "LC")
    sample_rate: Optional[int] = None  # Sample rate in Hz
    start_time: Optional[float] = None  # Start time of the audio stream in seconds
    tag_str: Optional[str] = None  # Codec tag string (e.g., "[0][0][0][0]")


class VideoInfo(BaseModel):
    """Video stream information extracted from the video file with ffprobe."""

    bit_depth: Optional[int] = None  # Bit depth per channel, 8, 10, 12, 16 etc.
    codec: Optional[str] = None  # Video codec used
    codec_long: Optional[str] = None  # Video codec detailed name
    codec_rfc6381: Optional[str] = None  # Video codec in RFC 6381 format
    duration_sec: Optional[float] = None  # Duration in seconds
    fps: Optional[float] = None  # Frames per second
    frame_count: Optional[int] = None  # Frames count
    height: Optional[int] = None  # Video frame height in pixels
    level: Optional[int] = None  # Video codec level
    pix_fmt: Optional[str] = None  # Pixel format (e.g., "yuv420p")
    profile: Optional[str] = None  # Video codec profile (e.g., "High")
    start_time: Optional[float] = None  # Start time of the video stream in seconds
    tag_str: Optional[str] = None  # Codec tag string (e.g., "[0][0][0][0]")
    width: Optional[int] = None  # Video frame width in pixels


def check_ffprobe():
    """Check if ffprobe is installed and available in PATH.
    :return: True if ffprobe is available, False otherwise
    :rtype: bool
    """
    try:
        # Try running `ffprobe -version` to see if it's installed
        subprocess.run(
            ["ffprobe", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        logger.debug("ffprobe is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Error: ffprobe is not installed")
        return False


def parse_audio_sr(audio_sr: Optional[str]) -> dict:
    """Parse a composite ``audio_sr``-style string into separate BIDS-style
    fields.

    Parses format like ``'48000Hz 16b 2ch aac'`` into individual fields.
    Returns ``n/a`` for all fields if parsing fails. This is the inverse of
    the composite string assembled in :func:`reprostim.video.audit.do_audit_file`
    for ``VaRecord.audio_sr`` (``f"{ai.sample_rate}Hz {ai.bits_per_sample}b
    {ai.channels}ch {ai.codec}"``); shared by any caller that needs to
    recover typed fields from that string (e.g. ``video.split``,
    ``bids.properties``).

    :param audio_sr: Composite audio-info string (e.g., ``'48000Hz 2ch
        aac'``), such as ``VaRecord.audio_sr`` or a ``SplitDevice``'s
        equivalent field.
    :type audio_sr: Optional[str]
    :return: Dict with ``audio_sample_rate``, ``audio_bit_depth``,
             ``audio_channel_count``, ``audio_codec`` (all strings, ``n/a``
             when not determined).
    :rtype: dict
    """
    na = {
        "audio_sample_rate": "n/a",
        "audio_bit_depth": "n/a",
        "audio_channel_count": "n/a",
        "audio_codec": "n/a",
    }
    if not audio_sr or audio_sr == "n/a":
        return na

    try:
        result = dict(na)
        for part in audio_sr.split():
            if part.endswith("Hz"):
                result["audio_sample_rate"] = part[:-2]
            elif part.endswith("b") and part[:-1].isdigit():
                result["audio_bit_depth"] = part[:-1]
            elif part.endswith("ch") and part[:-2].isdigit():
                result["audio_channel_count"] = part[:-2]
            else:
                result["audio_codec"] = part
        # hardcode bit depth to 16 if not parsed
        if result["audio_bit_depth"] == "n/a":
            result["audio_bit_depth"] = "16"
        return result
    except Exception:
        return na


def audio_codec_to_rfc6381(codec: str, profile: Optional[str]) -> Optional[str]:
    """Return the RFC 6381 codec string for an audio stream.

    :param codec: Short codec name as reported by ffprobe (e.g. ``"aac"``).
    :type codec: str

    :param profile: Codec profile string (e.g. ``"LC"``), or ``None``.
    :type profile: Optional[str]

    :return: RFC 6381 string (e.g. ``"mp4a.40.2"``), or ``None`` when the
             codec is not recognized.
    :rtype: Optional[str]
    """
    if codec == "aac":
        aot = {"LC": 2, "HE-AAC": 5, "HE-AACv2": 29, "LD": 23, "ELD": 39}.get(
            profile, 2
        )
        return f"mp4a.40.{aot}"
    if codec in ("mp3", "mp2"):
        return "mp4a.69"
    if codec == "opus":
        return "opus"
    return None


def video_codec_to_rfc6381(
    codec: str, profile: Optional[str], level: Optional[int]
) -> Optional[str]:
    """Return the RFC 6381 codec string for a video stream.

    :param codec: Short codec name as reported by ffprobe (e.g. ``"h264"``).
    :type codec: str

    :param profile: Codec profile string (e.g. ``"High"``), or ``None``.
    :type profile: Optional[str]

    :param level: Codec level integer as reported by ffprobe (e.g. ``42``),
                  or ``None``.
    :type level: Optional[int]

    :return: RFC 6381 string (e.g. ``"avc1.64002A"``), or ``None`` when the
             codec is not recognised.
    :rtype: Optional[str]
    """
    if codec == "h264":
        profile_idc = {
            "Baseline": 0x42,
            "Main": 0x4D,
            "High": 0x64,
            "High 10": 0x6E,
            "High 4:2:2": 0x7A,
            "High 4:4:4 Predictive": 0xF4,
        }.get(profile, 0x42)
        level_idc = level if level is not None else 0
        return f"avc1.{profile_idc:02X}00{level_idc:02X}"
    return None


def get_audio_video_info_ffprobe(
    path: str, count_frames: bool = False
) -> Tuple[AudioInfo, VideoInfo]:
    """Extract audio and video stream information from the video file using ffprobe.

    Issues a single ffprobe call that reads all streams, then splits results
    into an :class:`AudioInfo` (first audio stream) and a :class:`VideoInfo`
    (first video stream).

    :param path: Path to the video file (.mkv, .mp4, .avi)
    :type path: str
    :param count_frames: When ``True``, pass ``-count_frames`` to ``ffprobe``
        so it decodes the whole stream to report an exact ``nb_read_frames``
        count (populates ``VideoInfo.frame_count`` precisely, but is
        significantly slower — a full decode pass instead of just reading
        container metadata). When ``False`` (default), ``frame_count`` falls
        back to the container's ``nb_frames`` field, or an
        ``fps * duration_sec`` estimate, if available.
    :type count_frames: bool

    :return: Tuple of (AudioInfo, VideoInfo) with extracted stream information.
             Fields are ``None`` when the corresponding stream is absent or a
             value cannot be parsed.
    :rtype: Tuple[AudioInfo, VideoInfo]
    """

    logger.debug(f"get_audio_video_info_ffprobe: {path}")
    ai: AudioInfo = AudioInfo()
    vi: VideoInfo = VideoInfo()

    try:
        cmd = [
            "ffprobe",
            "-v",
            "quiet",  # suppress logs
            "-print_format",
            "json",  # JSON output
        ]
        if count_frames:
            cmd.append("-count_frames")
        cmd += [
            "-show_streams",  # streams
            path,
        ]
        # cmd = ["ffprobe", "-h"]
        logger.debug(f"run: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # logger.debug(f"ffprobe -> {result.stdout}")
        o = json.loads(result.stdout)
        logger.debug(f"ffprobe output: {o}")

        streams = o.get("streams", [])
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
        video_streams = [s for s in streams if s.get("codec_type") == "video"]

        if audio_streams:
            s = audio_streams[0]
            bps = s.get("bits_per_sample")
            if bps is not None and bps != 0:
                ai.bits_per_sample = bps
            ai.channels = s.get("channels")
            ai.codec = s.get("codec_name")
            ai.codec_long = s.get("codec_long_name")
            ai.profile = s.get("profile")
            ai.sample_rate = int(s["sample_rate"]) if "sample_rate" in s else None
            ai.start_time = float(s["start_time"]) if "start_time" in s else None
            ai.tag_str = s.get("codec_tag_string")
            ai.codec_rfc6381 = audio_codec_to_rfc6381(ai.codec or "", ai.profile)
            if "tags" in s and "DURATION" in s["tags"]:
                h, m, sec = s["tags"]["DURATION"].split(":")
                ai.duration_sec = int(h) * 3600 + int(m) * 60 + float(sec)
            elif "duration" in s:
                ai.duration_sec = float(s["duration"])

        if video_streams:
            s = video_streams[0]
            vi.codec = s.get("codec_name")
            vi.codec_long = s.get("codec_long_name")
            vi.profile = s.get("profile")
            vi.level = s.get("level")
            vi.width = s.get("width")
            vi.height = s.get("height")
            vi.pix_fmt = s.get("pix_fmt")
            vi.start_time = float(s["start_time"]) if "start_time" in s else None
            vi.tag_str = s.get("codec_tag_string")
            bprs = s.get("bits_per_raw_sample")
            if bprs is not None:
                try:
                    v = int(bprs)
                    if v != 0:
                        vi.bit_depth = v
                except (ValueError, TypeError):
                    pass
            for fps_key in ("avg_frame_rate", "r_frame_rate"):
                fps_str = s.get(fps_key)
                if fps_str and fps_str != "0/0":
                    try:
                        num, den = fps_str.split("/")
                        den_int = int(den)
                        if den_int != 0:
                            vi.fps = float(int(num)) / den_int
                            break
                    except (ValueError, ZeroDivisionError):
                        pass
            vi.codec_rfc6381 = video_codec_to_rfc6381(
                vi.codec or "", vi.profile, vi.level
            )
            if "tags" in s and "DURATION" in s["tags"]:
                h, m, sec = s["tags"]["DURATION"].split(":")
                vi.duration_sec = int(h) * 3600 + int(m) * 60 + float(sec)
            elif "duration" in s:
                vi.duration_sec = float(s["duration"])

            # nb_read_frames (from -count_frames, actual decoded count) is
            # preferred over nb_frames (container metadata, sometimes
            # missing/unreliable, e.g. "N/A") when both are present.
            for frame_count_key in ("nb_read_frames", "nb_frames"):
                try:
                    vi.frame_count = int(s[frame_count_key])
                    break
                except (KeyError, ValueError, TypeError):
                    continue
            if (
                vi.frame_count is None
                and vi.duration_sec is not None
                and vi.fps is not None
            ):
                # Exclude the stream's start offset within the container, if
                # any, for a more accurate estimate.
                dur_sec = vi.duration_sec
                if vi.start_time is not None and 0 < vi.start_time < dur_sec:
                    dur_sec -= vi.start_time
                vi.frame_count = round(dur_sec * vi.fps)

    except FileNotFoundError:
        logger.error("ffprobe is not installed or not in PATH")
    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe error: {e} {e.stdout} {e.stderr}")

    return ai, vi
