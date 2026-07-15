# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for reprostim.bids.inject_sidecar."""

import json
from unittest.mock import patch

import pytest

from reprostim.bids.inject_sidecar import (
    BisContext,
    ConflictPolicy,
    OverwriteMode,
    _do_sidecar,
    _do_sidecar_all,
    _error,
    _parse_ext_props,
    _verbose,
    do_main,
)

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
    assert ctx.dry_run is False
    assert ctx.verbose is False
    assert ctx.out_func is None
    assert ctx.ext_props == {}


def test_biscontext_custom_values():
    ctx = BisContext(
        mode=OverwriteMode.REPLACE,
        conflict_policy=ConflictPolicy.OVERWRITE,
        videos_tsv="videos.tsv",
        dry_run=True,
        verbose=True,
        out_func=print,
        ext_props={"TaskName": "rest"},
    )
    assert ctx.mode == OverwriteMode.REPLACE
    assert ctx.conflict_policy == ConflictPolicy.OVERWRITE
    assert ctx.videos_tsv == "videos.tsv"
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
# _do_sidecar
# ===========================================================================

_FFPROBE_PATCH = "reprostim.bids.inject_sidecar.bids_properties_from_ffprobe"


def test_do_sidecar_invalid_media_file_reports_error_and_returns_false(tmp_path):
    """A filename with no valid BIDS media-type suffix and an unknown
    extension fails the bmi.valid check before ffprobe is even consulted."""
    path = tmp_path / "randomname.xyz"
    path.touch()
    msgs = []
    ctx = BisContext(out_func=msgs.append)

    with patch(_FFPROBE_PATCH) as mock_ffprobe:
        result = _do_sidecar(ctx, str(path))

    assert result is False
    mock_ffprobe.assert_not_called()
    assert any("invalid BIDS media file" in m for m in msgs)


def test_do_sidecar_fresh_write(tmp_path):
    path = tmp_path / "sub-01_task-rest_recording-reprostim_video.mkv"
    path.touch()
    sidecar_path = path.with_suffix(".json")
    ctx = BisContext()

    with patch(_FFPROBE_PATCH, return_value={"AudioCodec": "aac"}):
        result = _do_sidecar(ctx, str(path))

    assert result is True
    assert json.loads(sidecar_path.read_text()) == {"AudioCodec": "aac"}


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
    filename) is counted as an error too, distinct from a missing path."""
    bad = tmp_path / "randomname.xyz"
    bad.touch()
    ctx = BisContext()

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
            dry_run=False,
            verbose=False,
            out_func=None,
        )

    assert rc == 0
    data = json.loads(sidecar_path.read_text())
    assert data == {"AudioCodec": "aac", "TaskName": "rest"}


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
            dry_run=False,
            verbose=False,
            out_func=None,
        )

    assert rc == 0
