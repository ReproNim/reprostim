# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

"""Tests for the YAML config support in reprostim.cli.entrypoint."""

from pathlib import Path
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from reprostim.cli import entrypoint
from reprostim.cli.entrypoint import (
    _find_default_config,
    _load_config,
    _validate_config_data,
    main,
)


def _write(tmp_path, text, name="config.yaml"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def _invoke_bids_inject(tmp_path, cli_args, config_args):
    """Invoke `reprostim [config_args] bids-inject ...` with do_main mocked."""
    videos = tmp_path / "videos.tsv"
    videos.write_text("")
    with patch("reprostim.bids.inject.do_main", return_value=0) as m:
        res = CliRunner().invoke(
            main,
            [*config_args, "bids-inject", str(tmp_path), "-f", str(videos), *cli_args],
        )
    return res, m


# ---------------------------------------------------------------------------
# _load_config
# ---------------------------------------------------------------------------


def test_load_config_global_and_command_sections(tmp_path):
    cfg = _write(
        tmp_path,
        "reprostim:\n  log_level: DEBUG\n"
        "bids_inject:\n  recursive: true\n  dataset: /x\n",
    )
    assert _load_config(cfg) == {
        "log_level": "DEBUG",
        "bids-inject": {"recursive": True, "dataset": "/x"},
    }


@pytest.mark.parametrize(
    "text,bad_names",
    [
        ("bids-inject:\n  recursive: true\n", ["bids-inject"]),
        ("reprostim:\n  log-level: DEBUG\n", ["log-level"]),
        ("bids_inject:\n  ignore-paths: [a]\n", ["ignore-paths"]),
        ("qr-parse:\nbids-inject:\n  buffer-before: 5\n", ["qr-parse", "bids-inject"]),
    ],
)
def test_load_config_dashed_names_rejected(tmp_path, text, bad_names):
    """Only snake_case names are in the schema, dashed ones are unknown."""
    cfg = _write(tmp_path, text)
    with pytest.raises(click.BadParameter) as e:
        _load_config(cfg)
    assert "Additional properties are not allowed" in e.value.message
    for n in bad_names:
        assert f"'{n}'" in e.value.message


def test_load_config_section_mapped_to_command_name(tmp_path):
    cfg = _write(tmp_path, "bids_inject:\n  ignore_paths: [a]\nqr_parse:\n  x: 1\n")
    assert _load_config(cfg) == {
        "bids-inject": {"ignore_paths": ["a"]},
        "qr-parse": {"x": 1},
    }


@pytest.mark.parametrize("text", ["", "# only comment\n", "bids_inject:\n"])
def test_load_config_empty_or_null_section(tmp_path, text):
    cfg = _write(tmp_path, text)
    assert _load_config(cfg) == {}


@pytest.mark.parametrize("text", ["- a\n- b\n", "just a string\n", "bids_inject: 5\n"])
def test_load_config_non_mapping_rejected(tmp_path, text):
    cfg = _write(tmp_path, text)
    with pytest.raises(click.BadParameter):
        _load_config(cfg)


# ---------------------------------------------------------------------------
# _find_default_config
# ---------------------------------------------------------------------------


def test_find_default_config_order_and_none(tmp_path, monkeypatch):
    first = tmp_path / "first.yaml"
    second = tmp_path / "second.yaml"
    monkeypatch.setattr(entrypoint, "DEFAULT_CONFIG_PATHS", (str(first), str(second)))
    assert _find_default_config() is None
    second.write_text("")
    assert _find_default_config() == str(second)
    first.write_text("")
    assert _find_default_config() == str(first)


def test_find_default_config_expands_user(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "cfg.yaml").write_text("")
    monkeypatch.setattr(entrypoint, "DEFAULT_CONFIG_PATHS", ("~/cfg.yaml",))
    assert _find_default_config() == str(tmp_path / "cfg.yaml")


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


def test_cli_config_overrides_defaults(tmp_path):
    cfg = _write(tmp_path, "bids_inject:\n  recursive: true\n  buffer_before: '5'\n")
    res, m = _invoke_bids_inject(tmp_path, [], ["-c", cfg])
    assert res.exit_code == 0, res.output
    assert m.call_args.kwargs["recursive"] is True
    assert m.call_args.kwargs["buffer_before"] == "5"


def test_cli_explicit_option_beats_config(tmp_path):
    cfg = _write(tmp_path, "bids_inject:\n  buffer_before: '5'\n")
    res, m = _invoke_bids_inject(tmp_path, ["-b", "9"], ["-c", cfg])
    assert res.exit_code == 0, res.output
    assert m.call_args.kwargs["buffer_before"] == "9"


def test_cli_config_missing_file_errors(tmp_path):
    res = CliRunner().invoke(main, ["-c", str(tmp_path / "nope.yaml"), "echo"])
    assert res.exit_code != 0


def test_cli_config_invalid_yaml_structure_errors(tmp_path):
    cfg = _write(tmp_path, "- a\n")
    res = CliRunner().invoke(main, ["-c", cfg, "echo"])
    assert res.exit_code != 0


def test_cli_config_ignore_paths_reach_do_main(tmp_path):
    cfg = _write(
        tmp_path,
        "bids_inject:\n  ignore_paths:\n    - sub-01/ses-01\n    - 'sub-02/*'\n",
    )
    res, m = _invoke_bids_inject(tmp_path, [], ["-c", cfg])
    assert res.exit_code == 0, res.output
    assert m.call_args.kwargs["ignore_paths"] == ["sub-01/ses-01", "sub-02/*"]


def test_cli_default_config_discovered(tmp_path, monkeypatch):
    cfg = _write(tmp_path, "bids_inject:\n  recursive: true\n")
    monkeypatch.setattr(entrypoint, "DEFAULT_CONFIG_PATHS", (cfg,))
    res, m = _invoke_bids_inject(tmp_path, [], [])
    assert res.exit_code == 0, res.output
    assert m.call_args.kwargs["recursive"] is True


def test_cli_no_config_keeps_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(entrypoint, "DEFAULT_CONFIG_PATHS", ())
    res, m = _invoke_bids_inject(tmp_path, [], [])
    assert res.exit_code == 0, res.output
    assert m.call_args.kwargs["recursive"] is False


def test_cli_unknown_section_rejected_by_schema(tmp_path):
    cfg = _write(tmp_path, "no_such_command:\n  x: 1\n")
    res, m = _invoke_bids_inject(tmp_path, [], ["-c", cfg])
    assert res.exit_code != 0
    assert "no_such_command" in res.output
    m.assert_not_called()


@pytest.mark.parametrize("name", ["reprostim_config_sample.yaml"])
def test_load_config_shipped_samples(name):
    """Sample configs under tests/data/ stay valid."""
    sample = Path(__file__).parent.parent / "data" / name
    assert "bids-inject" in _load_config(str(sample))


# ---------------------------------------------------------------------------
# LinkML schema validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("reprostim:\n  log_level: LOUD\n", "LOUD"),
        ("bids_inject:\n  ignore_path: [a]\n", "ignore_path"),
        ("bids_inject:\n  layout: weird\n", "weird"),
        ("bids_inject:\n  recursive: maybe\n", "maybe"),
        ("bids_inject:\n  buffer_before: soon\n", "soon"),
        ("bids_inject:\n  lock: yes\n", "lock"),  # unquoted yes -> boolean
    ],
)
def test_load_config_schema_violations_reported(tmp_path, text, expected):
    cfg = _write(tmp_path, text)
    with pytest.raises(click.BadParameter) as e:
        _load_config(cfg)
    assert expected in e.value.message
    assert cfg in e.value.message


def test_load_config_stub_sections_accept_any_content(tmp_path):
    cfg = _write(tmp_path, "split_video:\n  anything: [1, {a: b}]\nqr_parse:\n")
    assert _load_config(cfg) == {"split-video": {"anything": [1, {"a": "b"}]}}


def test_load_config_valid_quoted_lock_and_numeric_buffer(tmp_path):
    cfg = _write(
        tmp_path,
        "bids_inject:\n  lock: 'no'\n  buffer_before: 5\n  buffer_after: PT10S\n",
    )
    assert _load_config(cfg) == {
        "bids-inject": {"lock": "no", "buffer_before": 5, "buffer_after": "PT10S"}
    }


def test_cli_dashed_names_abort_command(tmp_path):
    cfg = _write(tmp_path, "bids-inject:\n  recursive: true\n")
    res, m = _invoke_bids_inject(tmp_path, [], ["-c", cfg])
    assert res.exit_code != 0
    assert "'bids-inject'" in res.output
    m.assert_not_called()


def test_cli_schema_error_aborts_command(tmp_path):
    cfg = _write(tmp_path, "bids_inject:\n  layout: weird\n")
    res, m = _invoke_bids_inject(tmp_path, [], ["-c", cfg])
    assert res.exit_code != 0
    assert "weird" in res.output
    m.assert_not_called()


# ---------------------------------------------------------------------------
# _validate_config_data (snake_case keys only)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"reprostim": {"log_level": "DEBUG"}},
        {"bids_inject": {"recursive": True, "ignore_paths": ["a", "b"]}},
        {"echo": {"anything": [1, 2]}},  # stub section accepts any content
    ],
)
def test_validate_config_data_valid(data):
    _validate_config_data(data, "cfg.yaml")  # must not raise


@pytest.mark.parametrize(
    "data, expected",
    [
        ({"reprostim": {"log_level": "LOUD"}}, "LOUD"),
        ({"reprostim": {"unknown_opt": 1}}, "unknown_opt"),
        ({"no_such_section": {}}, "no_such_section"),
        ({"bids_inject": {"recursive": "maybe"}}, "maybe"),
    ],
)
def test_validate_config_data_invalid(data, expected):
    with pytest.raises(click.BadParameter) as ei:
        _validate_config_data(data, "my_cfg.yaml")
    msg = ei.value.format_message()
    assert "my_cfg.yaml" in msg
    assert expected in msg
    assert ei.value.param_hint == "'-c' / '--config'"


@pytest.mark.parametrize(
    "data, bad_name",
    [
        ({"bids-inject": {}}, "bids-inject"),
        ({"reprostim": {"log-level": "DEBUG"}}, "log-level"),
    ],
)
def test_validate_config_data_dashed_names_rejected(data, bad_name):
    with pytest.raises(click.BadParameter) as ei:
        _validate_config_data(data, "cfg.yaml")
    msg = ei.value.format_message()
    assert "Additional properties are not allowed" in msg
    assert f"'{bad_name}'" in msg
    assert ei.value.param_hint == "'-c' / '--config'"


def test_validate_config_data_reports_all_errors():
    data = {"reprostim": {"log_level": "LOUD"}, "no_such_section": {}}
    with pytest.raises(click.BadParameter) as ei:
        _validate_config_data(data, "cfg.yaml")
    msg = ei.value.format_message()
    assert "LOUD" in msg and "no_such_section" in msg
