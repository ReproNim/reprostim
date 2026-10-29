# CLI YAML Config Task List

Tracks implementation progress against [config-spec.md](config-spec.md).

---

## Implementation

- [x] Global `-c / --config` option (eager, `expose_value=False`) on the `reprostim` group
- [x] `_load_config` — YAML → click `default_map` (`reprostim` section = global options,
      other sections = sub-commands)
- [x] ~~`-`/`_` key normalization~~ → replaced by snake_case-only names (dashed names rejected
      by the schema as unknown keys); sections `_` → `-` mapped to command names
- [x] Validation: top-level and section must be mappings (`click.BadParameter`)
- [x] Warn about unknown (non-command) sections; debug-log the loaded config path
- [x] Default config search (`reprostim_config.yaml`, `.reprostim/config.yaml`,
      `~/.reprostim/config.yaml`) via `_find_default_config`
- [x] Sample `tests/data/reprostim_config_sample.yaml`

- [x] LinkML schema `src/reprostim/schemas/config.linkml.yaml` (`reprostim`, `bids_inject`,
      stubs for other commands)
- [x] Validate loaded YAML against the schema (`_validate_config_data`), report errors as
      `click.BadParameter`; `linkml` added to dependencies
- [ ] Replace sub-command stubs with real schemas, one per command
- [x] Packaging: `reprostim/schemas/*.yaml` in the wheel `include`; `requests>=2.34.2` to avoid the
      `RequestsDependencyWarning` (chardet >= 6) triggered by the lazy `linkml` import
- [x] Pydantic model `src/reprostim/cli/config_model.py` generated from the schema
      (`make generate-config-model`, license header + module docstring, flake8 per-file ignore)
- [x] JSON schema for docs `docs/source/config/reprostim.schema.json` (`make generate-config-docs`);
      `make generate-config` does both

## Tests

Implemented in `tests/cli/test_entrypoint.py`.

- [x] `_load_config`: valid file → expected `default_map` (global keys flattened, command
      sections nested) (`test_load_config_global_and_command_sections`)
- [x] `_load_config`: dashed section/option names rejected by the schema
      (`test_load_config_dashed_names_rejected`, `test_cli_dashed_names_abort_command`);
      snake_case sections mapped to command names (`test_load_config_section_mapped_to_command_name`)
- [x] `_load_config`: empty file / `null` section → no error
      (`test_load_config_empty_or_null_section`)
- [x] `_load_config`: non-mapping top-level or section → `click.BadParameter`
      (`test_load_config_non_mapping_rejected`)
- [x] `-c` overrides option defaults of a sub-command (`test_cli_config_overrides_defaults`);
      explicit CLI option wins over config (`test_cli_explicit_option_beats_config`)
- [x] `-c` pointing to a missing file → Click error (`test_cli_config_missing_file_errors`);
      invalid structure → non-zero exit (`test_cli_config_invalid_yaml_structure_errors`)
- [x] `_find_default_config`: order of locations, none found → `None`, `~` expansion
      (`test_find_default_config_order_and_none`, `test_find_default_config_expands_user`)
- [x] Default config discovered / absent without `-c`
      (`test_cli_default_config_discovered`, `test_cli_no_config_keeps_defaults`)
- [x] Unknown section → rejected by schema validation, command not run
      (`test_cli_unknown_section_rejected_by_schema`)
- [x] `ignore_paths` list in `bids_inject` section reaches `do_main(ignore_paths=...)`
      (`test_cli_config_ignore_paths_reach_do_main`)
- [x] Shipped sample file `tests/data/reprostim_config_sample.yaml` loads without error
      (`test_load_config_shipped_samples`)

- [x] Schema validation: violations reported with file path and message
      (`test_load_config_schema_violations_reported`), stub sections accept any content,
      quoted `lock` / numeric buffer accepted, schema error aborts the command
      (`test_load_config_stub_sections_accept_any_content`,
      `test_load_config_valid_quoted_lock_and_numeric_buffer`, `test_cli_schema_error_aborts_command`)

- [x] `_validate_config_data` unit tests: valid configs, invalid values/keys/sections (path and
      message reported, hint `-c / --config`), all errors reported together, dashed names rejected
      (`test_validate_config_data_*`)

## Documentation

- [x] RTD "Configuration" section `docs/source/config/` (`index`, `reprostim`, `reprostim-schema`),
      linked from `docs/source/index.rst`; `sphinx-jsonschema` + `autodoc_pydantic` in `conf.py` /
      `docs/requirements.txt`
- [x] `cli.config_model` and `video.media_info` added to the API reference (`docs/source/api/index.rst`)
- [ ] Document default config locations (`DEFAULT_CONFIG_PATHS`) on the RTD `reprostim` config page
- [ ] CI check that `config_model.py` and `reprostim.schema.json` are in sync with the schema

## Open Questions / Future Work

- [x] Validate unknown keys inside known sections (LinkML schema)
- [x] ~~Generate/write Pydantic models with the same snake_case names~~ → generated
      (`config_model.py`); [ ] use it for runtime validation instead of / in addition to `linkml`
- [ ] Environment-variable override of config path
- [ ] Merge semantics across default locations
