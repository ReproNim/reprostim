# CLI YAML Config Specification

## Overview

`reprostim` accepts an optional YAML config file that overrides the default values of
global options and of any sub-command's options. Useful for per-dataset or per-site
settings (e.g. `bids-inject` dataset path, timezones, ignore lists) that would otherwise be
repeated on every command line.

Implemented in `src/reprostim/cli/entrypoint.py`.

## CLI

```
reprostim [-c / --config PATH] [OPTIONS] COMMAND ...
```

| Option                | Type                                   | Default | Description                                                                                  |
|-----------------------|----------------------------------------|---------|----------------------------------------------------------------------------------------------|
| `-c / --config PATH`  | Path (must exist, file, readable)      | none    | YAML config file. When omitted, the default locations below are probed (first match wins).   |

The option is `is_eager=True` and `expose_value=False`: its callback runs before other
options are parsed and populates `ctx.default_map`, which Click propagates to all
sub-commands through context inheritance.

## Default config search

When `-c` is not given, the first existing file of `DEFAULT_CONFIG_PATHS` is used:

1. `reprostim_config.yaml` (current directory)
2. `.reprostim/config.yaml` (current directory)
3. `~/.reprostim/config.yaml`

If none exists, no config is applied.

## File layout

```yaml
reprostim:            # global options of the main entrypoint
  log_level: DEBUG

bids_inject:          # section named after a sub-command (snake_case)
  dataset: /data/ds
  recursive: true
  ignore_paths:       # multiple=True options take a list
    - sub-01/ses-01
```

- Top-level section `reprostim` (`CONFIG_MAIN_SECTION`) holds options of the main group.
- Any other top-level section is a sub-command name in snake_case (`bids_inject` for the
  `bids-inject` command), holding that command's options. The loader maps `_` → `-` to get
  the Click command name used as the `default_map` key.
- A `null` section is skipped.

### Keys

- **Snake_case only.** All section and option names use `_`, never `-`: the schema, the
  generated Pydantic models, Click parameter names and the YAML keys share the same names.
  Names containing `-` are unknown to the schema and rejected with the generic schema error
  (`Additional properties are not allowed ('bids-inject' was unexpected)`). The CLI spellings
  (`--log-level`, `bids-inject`) differ from the YAML ones on purpose.
- Keys are Click **parameter names**, not necessarily the long option names: Click looks
  defaults up by parameter name.
- Beware options declared with an explicit parameter name, e.g. `--ignore-path` of
  `bids-inject` is parameter `ignore_paths`, so the key is `ignore_paths` (`ignore_path`
  is rejected by the schema).
- Explicit command-line options always take precedence over config values.

## Validation and logging

The parsed YAML is validated against the LinkML schema
`src/reprostim/schemas/config.linkml.yaml` (root class `ReprostimConfig`) in
`_validate_config_data`, called from `_load_config` after the top-level mapping check. LinkML
is used **only as a validator**: parsing/`default_map` building is unchanged. There is no
key normalization: the raw data is validated against the schema (slots are snake_case;
LinkML generators/validator cannot use dashed names), so dashed names fail as unknown keys.
`linkml` is imported lazily, only when a config is loaded. Any violation raises
`click.BadParameter` (`invalid config '<path>': - <message>`), aborting the command. The schema
fully describes `reprostim` and `bids_inject`; other sub-commands are stubs accepting any
content. Unknown sections/keys are rejected, so the "unknown section" warning below is
effectively superseded. `lock: yes` must be quoted (YAML 1.1 boolean).

| Condition                                         | Behavior                                                                  |
|---------------------------------------------------|---------------------------------------------------------------------------|
| Top-level YAML is not a mapping                   | `click.BadParameter` (hint `-c / --config`)                               |
| A section is not a mapping (and not `null`)       | `click.BadParameter`                                                      |
| Unknown section / key (incl. dashed names), bad value | `click.BadParameter` from schema validation                              |
| Section name is not a registered sub-command      | `logger.warning("Unknown section ...")` (only reachable for stub names)   |
| Config loaded                                     | `logger.debug("Found and loaded config yaml: <path>")`                    |

Unknown *keys* inside `reprostim` and `bids_inject` are rejected by the schema (stub
sections accept any content). Names with `-` are unknown keys and rejected the same way.

## Functions

| Function                                | Role                                                                          |
|-----------------------------------------|-------------------------------------------------------------------------------|
| `_find_default_config() -> str \| None` | Probe `DEFAULT_CONFIG_PATHS`, `~` expanded.                                   |
| `_validate_config_data(data, path)`     | LinkML schema validation, `click.BadParameter` on errors.                     |
| `_load_config(path) -> dict`            | Parse + validate YAML, return `default_map` (sections `_` → `-` command names). |
| `_config_callback(ctx, param, value)`   | Eager option callback; merges into `ctx.default_map`, stores path in `ctx.meta["reprostim.config"]`. |

## Schema and generated artifacts

The LinkML schema `src/reprostim/schemas/config.linkml.yaml` is the single source of truth
(shipped in the wheel via `reprostim/schemas/*.yaml`). Slots are snake_case Click parameter names.
Everything below is derived from it and regenerated through the `Makefile`:

| Artifact                                  | Command                          | Notes                                                                  |
|-------------------------------------------|----------------------------------|------------------------------------------------------------------------|
| `src/reprostim/cli/config_model.py`       | `make generate-config-model`     | `gen-pydantic --extra-fields forbid`, with license header and module docstring (SPDX/REUSE); run `isort`/`black` afterwards (pre-commit does it). **Do not edit manually.** Not used for runtime validation yet. |
| `docs/source/config/reprostim.schema.json`| `make generate-config-docs`      | `gen-json-schema`, committed so RTD does not need `linkml`.            |
| both                                      | `make generate-config`           |                                                                        |

Regenerate and commit both after every schema change. `.pre-commit-config.yaml` ignores `F401,E501`
for `config_model.py` (flake8). Slot/class `description`s end up in docstrings and `Field(description=...)`,
and are rendered as reStructuredText on RTD: escape markup, e.g. write ``` ``*_scans.tsv`` ```.

## Documentation (RTD)

- `docs/source/config/` (toctree entry in `docs/source/index.rst`): `index.rst`, `reprostim.rst`
  (hand-written format/overview, snake_case example), `reprostim-schema.rst` (`.. jsonschema::`
  directive rendering `reprostim.schema.json` via `sphinx-jsonschema`).
- `docs/source/api/index.rst` lists `cli.config_model` and `video.media_info`; the Pydantic model is
  rendered by `autodoc_pydantic` (`conf.py` hides JSON/config/validator summaries and the
  `linkml_meta` class variable).
- `docs/requirements.txt`: `autodoc_pydantic`, `sphinx-jsonschema`. RTD runs with
  `fail_on_warning: true`.

## Dependencies and packaging

- `linkml>=1.9.0` (validator, imported lazily) and `requests>=2.34.2` (older `requests` prints a
  `RequestsDependencyWarning` about `chardet>=6` pulled in with linkml) in `pyproject.toml`.
- `reprostim/schemas/*.yaml` is included in the wheel (`[tool.hatch.build.targets.wheel]`).

## Samples

- `tests/data/reprostim_config_sample.yaml` — minimal generic sample.

## Open Questions / TODOs

1. ~~Validate unknown keys inside known sections~~ → done via the LinkML schema.
2. Environment-variable override of the config path.
3. Merge (rather than first-match) semantics across default locations (user + project).
