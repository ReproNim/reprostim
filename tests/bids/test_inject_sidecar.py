# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for reprostim.bids.inject_sidecar."""

import json
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from reprostim.bids.inject_sidecar import (
    BisContext,
    ConflictPolicy,
    OverwriteMode,
    _do_sidecar,
    _do_sidecar_all,
    _error,
    _parse_ext_props,
    _verbose,
    _warn,
    do_main,
)
from reprostim.cli.cmd_bids_inject_sidecar import bids_inject_sidecar

# ===========================================================================
# OverwriteMode / ConflictPolicy
# ===========================================================================


def test_overwrite_mode_members():
    assert OverwriteMode.REPLACE.value == "replace"
    assert OverwriteMode.UPDATE.value == "update"


def test_conflict_policy_members():
    assert ConflictPolicy.ERROR.value == "error"
    assert ConflictPolicy.OVERWRITE.value == "overwrite"


# ===========================================================================
# BisContext
# ===========================================================================


def test_biscontext_defaults():
    ctx = BisContext()
    assert ctx.mode == OverwriteMode.UPDATE
    assert ctx.conflict_policy == ConflictPolicy.ERROR
    assert ctx.videos_tsv is None
    assert ctx.strict is False
    assert ctx.dry_run is False
    assert ctx.verbose is False
    assert ctx.out_func is None
    assert ctx.ext_props == {}


def test_biscontext_custom_values():
    ctx = BisContext(
        mode=OverwriteMode.REPLACE,
        conflict_policy=ConflictPolicy.OVERWRITE,
        videos_tsv="videos.tsv",
        strict=True,
        dry_run=True,
        verbose=True,
        out_func=print,
        ext_props={"TaskName": "rest"},
    )
    assert ctx.mode == OverwriteMode.REPLACE
    assert ctx.conflict_policy == ConflictPolicy.OVERWRITE
    assert ctx.videos_tsv == "videos.tsv"
    assert ctx.strict is True
    assert ctx.dry_run is True
    assert ctx.verbose is True
    assert ctx.out_func is print
    assert ctx.ext_props == {"TaskName": "rest"}


# ===========================================================================
# _parse_ext_props
# ===========================================================================


def test_parse_ext_props_plain_string_value():
    assert _parse_ext_props(["AudioCodec=aac"]) == {"AudioCodec": "aac"}


def test_parse_ext_props_json_numeric_value_is_typed():
    assert _parse_ext_props(["RecordingDuration=3600"]) == {"RecordingDuration": 3600}
    assert isinstance(
        _parse_ext_props(["RecordingDuration=3600"])["RecordingDuration"], int
    )


def test_parse_ext_props_json_object_value():
    result = _parse_ext_props(['ExtraInfo={"key": "val", "num": 5}'])
    assert result == {"ExtraInfo": {"key": "val", "num": 5}}


def test_parse_ext_props_bare_json_object_merges_top_level_keys():
    result = _parse_ext_props(['{"AudioCodec": "aac", "AudioSampleRate": 48000}'])
    assert result == {"AudioCodec": "aac", "AudioSampleRate": 48000}


def test_parse_ext_props_bare_json_object_wins_over_equals_split():
    """A bare JSON object entry is detected before attempting to split on
    '=', even if its content contains a literal '='."""
    result = _parse_ext_props(['{"Note": "x=y"}'])
    assert result == {"Note": "x=y"}


def test_parse_ext_props_multiple_entries_last_wins():
    result = _parse_ext_props(['{"AudioCodec": "aac"}', "AudioCodec=override"])
    assert result == {"AudioCodec": "override"}


def test_parse_ext_props_multiple_meta_value_entries_accumulate():
    result = _parse_ext_props(["AudioCodec=aac", "RecordingDuration=3600"])
    assert result == {"AudioCodec": "aac", "RecordingDuration": 3600}


def test_parse_ext_props_empty_list_returns_empty_dict():
    assert _parse_ext_props([]) == {}


def test_parse_ext_props_malformed_no_equals_raises():
    with pytest.raises(ValueError, match="expected META=VALUE"):
        _parse_ext_props(["no-equals-no-json"])


def test_parse_ext_props_empty_meta_raises():
    with pytest.raises(ValueError, match="empty META name"):
        _parse_ext_props(["=novalue"])


# ===========================================================================
# _error
# ===========================================================================


def test_error_calls_out_func_with_prefix():
    msgs = []
    ctx = BisContext(out_func=msgs.append)
    _error(ctx, "something broke")
    assert msgs == ["Error: something broke"]


def test_error_no_out_func_does_not_raise():
    ctx = BisContext(out_func=None)
    _error(ctx, "something broke")  # should not raise


def test_error_returns_none():
    ctx = BisContext(out_func=lambda m: None)
    assert _error(ctx, "x") is None


# ===========================================================================
# _verbose
# ===========================================================================


def test_verbose_reports_when_verbose_true():
    msgs = []
    ctx = BisContext(verbose=True, out_func=msgs.append)
    _verbose(ctx, "detail")
    assert msgs == ["detail"]


def test_verbose_silent_when_verbose_false():
    msgs = []
    ctx = BisContext(verbose=False, out_func=msgs.append)
    _verbose(ctx, "detail")
    assert msgs == []


def test_verbose_no_out_func_does_not_raise():
    ctx = BisContext(verbose=True, out_func=None)
    _verbose(ctx, "detail")  # should not raise


# ===========================================================================
# _warn
# ===========================================================================


def test_warn_calls_out_func_with_prefix_regardless_of_verbose():
    msgs = []
    ctx = BisContext(verbose=False, out_func=msgs.append)
    _warn(ctx, "heads up")
    assert msgs == ["Warn: heads up"]


def test_warn_no_out_func_does_not_raise():
    ctx = BisContext(out_func=None)
    _warn(ctx, "heads up")  # should not raise


def test_warn_returns_none():
    ctx = BisContext(out_func=lambda m: None)
    assert _warn(ctx, "x") is None


# ===========================================================================
# _do_sidecar
# ===========================================================================

_FFPROBE_PATCH = "reprostim.bids.inject_sidecar.bids_properties_from_ffprobe"
_VIDEO_AUDIT_PATCH = "reprostim.bids.inject_sidecar.bids_properties_from_video_audit"


def test_do_sidecar_invalid_media_file_strict_reports_error_and_returns_false(
    tmp_path,
):
    """In strict mode, a filename with no valid BIDS media-type suffix and an
    unknown extension fails the bmi.valid check before ffprobe is even
    consulted."""
    path = tmp_path / "randomname.xyz"
    path.touch()
    msgs = []
    ctx = BisContext(strict=True, out_func=msgs.append)

    with patch(_FFPROBE_PATCH) as mock_ffprobe:
        result = _do_sidecar(ctx, str(path))

    assert result is False
    mock_ffprobe.assert_not_called()
    assert any("Error:" in m and "invalid BIDS media file" in m for m in msgs)


def test_do_sidecar_invalid_media_file_non_strict_warns_and_continues(
    tmp_path,
):
    """By default (non-strict), the same invalid-bmi problem is only reported
    as a warning and processing continues through to a written sidecar."""
    path = tmp_path / "randomname.xyz"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    msgs = []
    ctx = BisContext(out_func=msgs.append)

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        result = _do_sidecar(ctx, str(path))

    assert result is True
    assert any("Warn:" in m and "invalid BIDS media file" in m for m in msgs)
    assert not any(m.startswith("Error:") for m in msgs)
    assert json.loads(sidecar_path.read_text()) == {"AudioCodec": "aac"}


def test_do_sidecar_fresh_write(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    ctx = BisContext()

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        result = _do_sidecar(ctx, str(path))

    assert result is True
    assert json.loads(sidecar_path.read_text()) == {"AudioCodec": "aac"}


def test_do_sidecar_videos_tsv_uses_video_audit_not_ffprobe(tmp_path):
    """When ctx.videos_tsv is set, extraction prefers
    bids_properties_from_video_audit and never calls ffprobe."""
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    ctx = BisContext(videos_tsv=str(tmp_path / "videos.tsv"))

    with patch(
        _VIDEO_AUDIT_PATCH, return_value={"AudioCodec": "aac"}
    ) as mock_va, patch(_FFPROBE_PATCH) as mock_ffprobe:
        result = _do_sidecar(ctx, str(path))

    assert result is True
    mock_va.assert_called_once_with(str(path), ctx.videos_tsv)
    mock_ffprobe.assert_not_called()
    assert json.loads(sidecar_path.read_text()) == {"AudioCodec": "aac"}


def test_do_sidecar_videos_tsv_failure_falls_back_to_ffprobe(tmp_path):
    """If bids_properties_from_video_audit raises, extraction rolls back to
    the plain ffprobe-based approach for that file, with a warning."""
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    msgs = []
    ctx = BisContext(videos_tsv=str(tmp_path / "videos.tsv"), out_func=msgs.append)

    with patch(_VIDEO_AUDIT_PATCH, side_effect=RuntimeError("boom")), patch(
        _FFPROBE_PATCH, return_value={"AudioCodec": "aac"}
    ) as mock_ffprobe:
        result = _do_sidecar(ctx, str(path))

    assert result is True
    mock_ffprobe.assert_called_once_with(str(path))
    assert any("Warn:" in m and "falling back to ffprobe" in m for m in msgs)
    assert json.loads(sidecar_path.read_text()) == {"AudioCodec": "aac"}


def test_do_sidecar_no_videos_tsv_uses_ffprobe_only(tmp_path):
    """Without ctx.videos_tsv, bids_properties_from_video_audit is never
    consulted (unchanged, ffprobe-only behavior)."""
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    ctx = BisContext()

    with patch(_VIDEO_AUDIT_PATCH) as mock_va, patch(
        _FFPROBE_PATCH, return_value={"AudioCodec": "aac"}
    ):
        _do_sidecar(ctx, str(path))

    mock_va.assert_not_called()


def test_do_sidecar_ext_props_override_extracted_fields(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    ctx = BisContext(ext_props={"AudioCodec": "override"})

    with patch(
        _FFPROBE_PATCH, return_value={"AudioCodec": "aac", "VideoCodec": "h264"}
    ):
        _do_sidecar(ctx, str(path))

    data = json.loads(sidecar_path.read_text())
    assert data == {"AudioCodec": "override", "VideoCodec": "h264"}


def test_do_sidecar_update_mode_preserves_unrelated_existing_keys(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    sidecar_path.write_text(json.dumps({"CustomField": "keep-me"}))
    ctx = BisContext(mode=OverwriteMode.UPDATE)

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        result = _do_sidecar(ctx, str(path))

    assert result is True
    data = json.loads(sidecar_path.read_text())
    assert data == {"CustomField": "keep-me", "AudioCodec": "aac"}


def test_do_sidecar_replace_mode_discards_unrelated_existing_keys(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    sidecar_path.write_text(json.dumps({"CustomField": "should-vanish"}))
    ctx = BisContext(mode=OverwriteMode.REPLACE)

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        result = _do_sidecar(ctx, str(path))

    assert result is True
    data = json.loads(sidecar_path.read_text())
    assert data == {"AudioCodec": "aac"}


def test_do_sidecar_no_conflict_when_new_value_matches_existing(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    sidecar_path.write_text(json.dumps({"AudioCodec": "aac"}))
    ctx = BisContext()

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        result = _do_sidecar(ctx, str(path))

    assert result is True
    assert json.loads(sidecar_path.read_text()) == {"AudioCodec": "aac"}


def test_do_sidecar_no_conflict_when_existing_is_na(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    sidecar_path.write_text(json.dumps({"AudioCodec": "n/a"}))
    ctx = BisContext()

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        result = _do_sidecar(ctx, str(path))

    assert result is True
    assert json.loads(sidecar_path.read_text()) == {"AudioCodec": "aac"}


def test_do_sidecar_conflict_error_policy_aborts_without_writing(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    sidecar_path.write_text(json.dumps({"AudioCodec": "aac"}))
    msgs = []
    ctx = BisContext(conflict_policy=ConflictPolicy.ERROR, out_func=msgs.append)

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "totallydifferent"}):
        result = _do_sidecar(ctx, str(path))

    assert result is False
    # Sidecar left untouched.
    assert json.loads(sidecar_path.read_text()) == {"AudioCodec": "aac"}
    assert any("conflicting value" in m for m in msgs)


def test_do_sidecar_conflict_overwrite_policy_writes_and_warns(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    sidecar_path.write_text(json.dumps({"AudioCodec": "aac"}))
    msgs = []
    ctx = BisContext(
        conflict_policy=ConflictPolicy.OVERWRITE, verbose=True, out_func=msgs.append
    )

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "totallydifferent"}):
        result = _do_sidecar(ctx, str(path))

    assert result is True
    assert json.loads(sidecar_path.read_text()) == {"AudioCodec": "totallydifferent"}
    assert any("overwriting" in m for m in msgs)


def test_do_sidecar_real_downgrade_to_na_is_conflict_under_error_policy(tmp_path):
    """existing real value + new 'n/a' behaves like the general 'differs'
    case: error policy aborts by default."""
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    sidecar_path.write_text(json.dumps({"AudioCodec": "aac"}))
    ctx = BisContext(conflict_policy=ConflictPolicy.ERROR)

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "n/a"}):
        result = _do_sidecar(ctx, str(path))

    assert result is False
    assert json.loads(sidecar_path.read_text()) == {"AudioCodec": "aac"}


def test_do_sidecar_malformed_existing_json_update_mode_errors(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    sidecar_path.write_text("{not valid json")
    msgs = []
    ctx = BisContext(mode=OverwriteMode.UPDATE, out_func=msgs.append)

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        result = _do_sidecar(ctx, str(path))

    assert result is False
    assert any("failed to read existing sidecar" in m for m in msgs)
    # File left untouched (no partial write).
    assert sidecar_path.read_text() == "{not valid json"


def test_do_sidecar_replace_mode_ignores_malformed_existing_json(tmp_path):
    """replace mode never reads existing content, so malformed JSON there
    isn't even an error."""
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    sidecar_path.write_text("{not valid json")
    ctx = BisContext(mode=OverwriteMode.REPLACE)

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        result = _do_sidecar(ctx, str(path))

    assert result is True
    assert json.loads(sidecar_path.read_text()) == {"AudioCodec": "aac"}


def test_do_sidecar_dry_run_prints_and_does_not_write(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    msgs = []
    ctx = BisContext(dry_run=True, out_func=msgs.append)

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        result = _do_sidecar(ctx, str(path))

    assert result is True
    assert not sidecar_path.exists()
    assert any(m.startswith("[DRY-RUN]") for m in msgs)


def test_do_sidecar_dry_run_no_out_func_does_not_raise(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    ctx = BisContext(dry_run=True, out_func=None)

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        result = _do_sidecar(ctx, str(path))

    assert result is True
    assert not path.with_suffix(".json").exists()


def test_do_sidecar_write_oserror_reports_error(tmp_path):
    """When the sidecar path is a directory, the write raises OSError,
    which is caught and reported rather than propagating."""
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    sidecar_path.mkdir()
    msgs = []
    ctx = BisContext(out_func=msgs.append)

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        result = _do_sidecar(ctx, str(path))

    assert result is False
    assert any("failed to write sidecar" in m for m in msgs)


def test_do_sidecar_verbose_reports_wrote_fields(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    msgs = []
    ctx = BisContext(verbose=True, out_func=msgs.append)

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        _do_sidecar(ctx, str(path))

    assert any("wrote 1 fields" in m for m in msgs)


# ===========================================================================
# _do_sidecar_all
# ===========================================================================


def test_do_sidecar_all_counts_errors_and_skips_invalid_paths(tmp_path):
    good = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    good.touch()
    missing = str(tmp_path / "does-not-exist.mkv")
    ctx = BisContext()

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        errors = _do_sidecar_all(ctx, [str(good), missing])

    assert errors == 1
    assert good.with_suffix(".json").exists()


def test_do_sidecar_all_counts_a_failing_existing_file(tmp_path):
    """An existing file that _do_sidecar itself rejects (invalid BIDS
    filename, strict mode) is counted as an error too, distinct from a
    missing path."""
    bad = tmp_path / "randomname.xyz"
    bad.touch()
    ctx = BisContext(strict=True)

    with patch(_FFPROBE_PATCH) as mock_ffprobe:
        errors = _do_sidecar_all(ctx, [str(bad)])

    assert errors == 1
    mock_ffprobe.assert_not_called()


def test_do_sidecar_all_zero_errors_when_all_succeed(tmp_path):
    a = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    b = tmp_path / "sub-01_task-rest_recording-reprostim_audio.wav"
    a.touch()
    b.touch()
    ctx = BisContext()

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        errors = _do_sidecar_all(ctx, [str(a), str(b)])

    assert errors == 0


# ===========================================================================
# do_main
# ===========================================================================


def test_do_main_malformed_add_returns_1_before_any_processing(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    msgs = []

    with patch(_FFPROBE_PATCH) as mock_ffprobe:
        rc = do_main(
            files=[str(path)],
            videos=None,
            mode="update",
            add_meta=["no-equals-no-json"],
            existing_different="error",
            strict=False,
            dry_run=False,
            verbose=False,
            out_func=msgs.append,
        )

    assert rc == 1
    mock_ffprobe.assert_not_called()
    assert any("Error:" in m for m in msgs)


def test_do_main_malformed_add_no_out_func_does_not_raise(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()

    with patch(_FFPROBE_PATCH) as mock_ffprobe:
        rc = do_main(
            files=[str(path)],
            videos=None,
            mode="update",
            add_meta=["no-equals-no-json"],
            existing_different="error",
            strict=False,
            dry_run=False,
            verbose=False,
            out_func=None,
        )

    assert rc == 1
    mock_ffprobe.assert_not_called()


def test_do_main_success_returns_0_with_summary(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    msgs = []

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        rc = do_main(
            files=[str(path)],
            videos=None,
            mode="update",
            add_meta=[],
            existing_different="error",
            strict=False,
            dry_run=False,
            verbose=False,
            out_func=msgs.append,
        )

    assert rc == 0
    assert "1 processed, 1 written, 0 errors" in msgs


def test_do_main_errors_return_1_with_summary_counts(tmp_path):
    good = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    good.touch()
    missing = str(tmp_path / "does-not-exist.mkv")
    msgs = []

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        rc = do_main(
            files=[str(good), missing],
            videos=None,
            mode="update",
            add_meta=[],
            existing_different="error",
            strict=False,
            dry_run=False,
            verbose=False,
            out_func=msgs.append,
        )

    assert rc == 1
    assert "2 processed, 1 written, 1 errors" in msgs


def test_do_main_dry_run_prefix_in_summary(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    msgs = []

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        rc = do_main(
            files=[str(path)],
            videos=None,
            mode="update",
            add_meta=[],
            existing_different="error",
            strict=False,
            dry_run=True,
            verbose=False,
            out_func=msgs.append,
        )

    assert rc == 0
    assert "[DRY-RUN] 1 processed, 1 written, 0 errors" in msgs
    assert not path.with_suffix(".json").exists()


def test_do_main_add_meta_flows_into_sidecar(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        rc = do_main(
            files=[str(path)],
            videos=None,
            mode="update",
            add_meta=["TaskName=rest"],
            existing_different="error",
            strict=False,
            dry_run=False,
            verbose=False,
            out_func=None,
        )

    assert rc == 0
    data = json.loads(sidecar_path.read_text())
    assert data == {"AudioCodec": "aac", "TaskName": "rest"}


def test_do_main_strict_invalid_media_file_errors(tmp_path):
    path = tmp_path / "randomname.xyz"
    path.touch()
    msgs = []

    with patch(_FFPROBE_PATCH) as mock_ffprobe:
        rc = do_main(
            files=[str(path)],
            videos=None,
            mode="update",
            add_meta=[],
            existing_different="error",
            strict=True,
            dry_run=False,
            verbose=False,
            out_func=msgs.append,
        )

    assert rc == 1
    mock_ffprobe.assert_not_called()
    assert "1 processed, 0 written, 1 errors" in msgs


def test_do_main_non_strict_invalid_media_file_still_processed(tmp_path):
    path = tmp_path / "randomname.xyz"
    path.touch()
    msgs = []

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        rc = do_main(
            files=[str(path)],
            videos=None,
            mode="update",
            add_meta=[],
            existing_different="error",
            strict=False,
            dry_run=False,
            verbose=False,
            out_func=msgs.append,
        )

    assert rc == 0
    assert "1 processed, 1 written, 0 errors" in msgs
    assert any("Warn:" in m and "invalid BIDS media file" in m for m in msgs)


def test_do_main_no_out_func_does_not_raise(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        rc = do_main(
            files=[str(path)],
            videos=None,
            mode="update",
            add_meta=[],
            existing_different="error",
            strict=False,
            dry_run=False,
            verbose=False,
            out_func=None,
        )

    assert rc == 0


# ===========================================================================
# CLI tests (Click CliRunner) for cmd_bids_inject_sidecar
# ===========================================================================

_CLI_DO_MAIN_PATCH = "reprostim.bids.inject_sidecar.do_main"


@pytest.fixture()
def media_file(tmp_path):
    """A file with a valid BIDS media-type suffix, so it passes both Click's
    exists=True check and the bmi.valid check inside _do_sidecar."""
    f = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    f.touch()
    return f


def test_cli_help_renders_without_error():
    result = CliRunner().invoke(bids_inject_sidecar, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_cli_missing_files_argument_nonzero_exit():
    result = CliRunner().invoke(bids_inject_sidecar, [])
    assert result.exit_code != 0
    assert "missing" in result.output.lower()


def test_cli_nonexistent_file_argument_nonzero_exit(tmp_path):
    missing = str(tmp_path / "does-not-exist.mkv")
    result = CliRunner().invoke(bids_inject_sidecar, [missing])
    assert result.exit_code != 0
    assert "does not exist" in result.output.lower()


def test_cli_unknown_mode_value_errors(media_file):
    result = CliRunner().invoke(
        bids_inject_sidecar, ["--mode", "bogus", str(media_file)]
    )
    assert result.exit_code != 0
    assert "invalid choice" in result.output.lower() or "invalid value" in (
        result.output.lower()
    )


def test_cli_unknown_existing_different_value_errors(media_file):
    result = CliRunner().invoke(
        bids_inject_sidecar, ["--existing-different", "bogus", str(media_file)]
    )
    assert result.exit_code != 0
    assert "invalid choice" in result.output.lower() or "invalid value" in (
        result.output.lower()
    )


def test_cli_nonexistent_videos_path_nonzero_exit(media_file, tmp_path):
    missing_videos = str(tmp_path / "videos.tsv")
    result = CliRunner().invoke(
        bids_inject_sidecar, ["--videos", missing_videos, str(media_file)]
    )
    assert result.exit_code != 0
    assert "does not exist" in result.output.lower()


def test_cli_multiple_add_options_accumulate(media_file):
    with patch(_CLI_DO_MAIN_PATCH, return_value=0) as mock_dm:
        CliRunner().invoke(
            bids_inject_sidecar,
            [
                "--add",
                "TaskName=rest",
                "--add",
                "RecordingDuration=3600",
                str(media_file),
            ],
        )
    mock_dm.assert_called_once()
    assert mock_dm.call_args.kwargs["add_meta"] == [
        "TaskName=rest",
        "RecordingDuration=3600",
    ]


def test_cli_files_passed_as_list_to_do_main(tmp_path):
    a = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    b = tmp_path / "sub-01_task-rest_recording-reprostim_audio.wav"
    a.touch()
    b.touch()

    with patch(_CLI_DO_MAIN_PATCH, return_value=0) as mock_dm:
        CliRunner().invoke(bids_inject_sidecar, [str(a), str(b)])

    mock_dm.assert_called_once()
    assert mock_dm.call_args.kwargs["files"] == [str(a), str(b)]


def test_cli_mode_default_passed_to_do_main(media_file):
    with patch(_CLI_DO_MAIN_PATCH, return_value=0) as mock_dm:
        CliRunner().invoke(bids_inject_sidecar, [str(media_file)])
    assert mock_dm.call_args.kwargs["mode"] == "update"


def test_cli_mode_custom_passed_to_do_main(media_file):
    with patch(_CLI_DO_MAIN_PATCH, return_value=0) as mock_dm:
        CliRunner().invoke(bids_inject_sidecar, ["-m", "replace", str(media_file)])
    assert mock_dm.call_args.kwargs["mode"] == "replace"


def test_cli_existing_different_default_passed_to_do_main(media_file):
    with patch(_CLI_DO_MAIN_PATCH, return_value=0) as mock_dm:
        CliRunner().invoke(bids_inject_sidecar, [str(media_file)])
    assert mock_dm.call_args.kwargs["existing_different"] == "error"


def test_cli_existing_different_custom_passed_to_do_main(media_file):
    with patch(_CLI_DO_MAIN_PATCH, return_value=0) as mock_dm:
        CliRunner().invoke(bids_inject_sidecar, ["-e", "overwrite", str(media_file)])
    assert mock_dm.call_args.kwargs["existing_different"] == "overwrite"


def test_cli_strict_flag_default_false(media_file):
    with patch(_CLI_DO_MAIN_PATCH, return_value=0) as mock_dm:
        CliRunner().invoke(bids_inject_sidecar, [str(media_file)])
    assert mock_dm.call_args.kwargs["strict"] is False


def test_cli_strict_flag_set_true(media_file):
    with patch(_CLI_DO_MAIN_PATCH, return_value=0) as mock_dm:
        CliRunner().invoke(bids_inject_sidecar, ["-s", str(media_file)])
    assert mock_dm.call_args.kwargs["strict"] is True


def test_cli_dry_run_flag_default_false(media_file):
    with patch(_CLI_DO_MAIN_PATCH, return_value=0) as mock_dm:
        CliRunner().invoke(bids_inject_sidecar, [str(media_file)])
    assert mock_dm.call_args.kwargs["dry_run"] is False


def test_cli_dry_run_flag_set_true(media_file):
    with patch(_CLI_DO_MAIN_PATCH, return_value=0) as mock_dm:
        CliRunner().invoke(bids_inject_sidecar, ["-d", str(media_file)])
    assert mock_dm.call_args.kwargs["dry_run"] is True


def test_cli_verbose_flag_default_false(media_file):
    with patch(_CLI_DO_MAIN_PATCH, return_value=0) as mock_dm:
        CliRunner().invoke(bids_inject_sidecar, [str(media_file)])
    assert mock_dm.call_args.kwargs["verbose"] is False


def test_cli_verbose_flag_set_true(media_file):
    with patch(_CLI_DO_MAIN_PATCH, return_value=0) as mock_dm:
        CliRunner().invoke(bids_inject_sidecar, ["-v", str(media_file)])
    assert mock_dm.call_args.kwargs["verbose"] is True


def test_cli_videos_option_passed_to_do_main(media_file, tmp_path):
    videos_tsv = tmp_path / "videos.tsv"
    videos_tsv.touch()

    with patch(_CLI_DO_MAIN_PATCH, return_value=0) as mock_dm:
        CliRunner().invoke(
            bids_inject_sidecar, ["-f", str(videos_tsv), str(media_file)]
        )
    assert mock_dm.call_args.kwargs["videos"] == str(videos_tsv)


def test_cli_videos_default_none(media_file):
    with patch(_CLI_DO_MAIN_PATCH, return_value=0) as mock_dm:
        CliRunner().invoke(bids_inject_sidecar, [str(media_file)])
    assert mock_dm.call_args.kwargs["videos"] is None


def test_cli_out_func_is_click_echo(media_file):
    with patch(_CLI_DO_MAIN_PATCH, return_value=0) as mock_dm:
        CliRunner().invoke(bids_inject_sidecar, [str(media_file)])
    assert mock_dm.call_args.kwargs["out_func"] is click.echo


def test_cli_verbose_prints_completion_summary(media_file):
    with patch(_CLI_DO_MAIN_PATCH, return_value=0):
        result = CliRunner().invoke(bids_inject_sidecar, ["-v", str(media_file)])
    assert "completed in" in result.output


def test_cli_non_verbose_omits_completion_summary(media_file):
    with patch(_CLI_DO_MAIN_PATCH, return_value=0):
        result = CliRunner().invoke(bids_inject_sidecar, [str(media_file)])
    assert "completed in" not in result.output


# --- End-to-end (real do_main, mocked ffprobe only) ---


def test_cli_end_to_end_success_exit_code_zero(media_file):
    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        result = CliRunner().invoke(bids_inject_sidecar, [str(media_file)])

    assert result.exit_code == 0
    assert json.loads(media_file.with_suffix(".json").read_text()) == {
        "AudioCodec": "aac"
    }


def test_cli_end_to_end_strict_invalid_file_nonzero_exit(tmp_path):
    bad = tmp_path / "randomname.xyz"
    bad.touch()

    with patch(_FFPROBE_PATCH) as mock_ffprobe:
        result = CliRunner().invoke(bids_inject_sidecar, ["--strict", str(bad)])

    assert result.exit_code != 0
    mock_ffprobe.assert_not_called()
    assert "1 processed, 0 written, 1 errors" in result.output


def test_cli_end_to_end_one_bad_file_does_not_stop_batch(tmp_path):
    good = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    bad = tmp_path / "randomname.xyz"
    good.touch()
    bad.touch()

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        result = CliRunner().invoke(
            bids_inject_sidecar, ["--strict", str(bad), str(good)]
        )

    assert result.exit_code != 0
    assert "2 processed, 1 written, 1 errors" in result.output
    assert json.loads(good.with_suffix(".json").read_text()) == {"AudioCodec": "aac"}
