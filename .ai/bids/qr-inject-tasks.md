# `bids-qr-inject` Task List

Tracks implementation progress against [qr-inject-spec.md](qr-inject-spec.md).

**Status: specification only — no code written yet.** Everything below is unchecked, except the
spec/tasks documents themselves. Items marked *(proposal)* come from the spec's own design and
need confirmation first (see spec "Open Questions / TODOs").

---

## Design decisions to settle first

- [ ] Confirm new command `bids-qr-inject` vs an extra mode of `bids-inject` (spec Open Question #1)
- [ ] Choose QR source for `auto`/`embed-existing`: per-source JSONL with re-basing vs per-clip JSONL (#2)
- [ ] Decide the final suffix of the QR events file (`_events` placeholder vs `_qrcodes`/`_qr`/…) (#3)
- [ ] Decide date-anonymization details: `strip` placeholder date, sanitizing dates inside `data` (#4)
- [ ] Decide `events.json` placement (per recording vs dataset level) (#5)
- [ ] Decide column naming/prefix for the new `_scans.tsv` columns (#6) and `onset` semantics (#7)

## Spec / docs

- [x] `.ai/bids/qr-inject-spec.md`
- [x] `.ai/bids/qr-inject-tasks.md`
- [ ] Add `bids-qr-inject` entries to `.ai/context.md` once code exists
- [ ] Update `inject-spec.md` / `inject-tasks.md` "Future (`bids-qr-inject`)" notes to link here
- [ ] `docs/source/cli/bids-qr-inject.rst` (+ `cli/index.rst`) and changelog entry

## CLI Options (`cli/cmd_bids_qr_inject.py`)

- [ ] `PATHS` argument — `_scans.tsv` files or directories, same rules as `bids-inject`
- [ ] `-d / --dataset PATH` — default `.`; `do_main` re-validates it exists (like `bids-inject`)
- [ ] `-r / --recursive`
- [ ] `-f / --videos PATH` — optional `videos.tsv`
- [ ] `-q / --qr [auto|embed-existing|parse]` — default `auto` *(proposal)*
- [ ] `-m / --match REGEX`
- [ ] `-i / --ignore-path PATH_OR_GLOB` — repeatable
- [ ] `--anonymize-dates [strip|none|offset]` — default `strip`
- [ ] `--date-offset DAYS` — required with `offset`; error otherwise
- [ ] `-w / --overwrite [skip|force|always|error]`
- [ ] `-n / --dry-run`
- [ ] `-v / --verbose`
- [ ] Register command in `entrypoint.py`; propagate result with `ctx.exit(res)` (not `return res`)
- [ ] `--lock [yes|no]` if `--videos` is used (spec Open Question #10)

## Core logic (`bids/qr_inject.py`)

### Context / enums
- [ ] `QiContext` (mirrors `BiContext`/`BisContext`): dataset home, `videos_tsv`, `qr` mode,
      `match`, `ignore_paths`, anonymization mode + offset, overwrite policy, `dry_run`,
      `verbose`, `out_func`
- [ ] Enums for `--qr`, `--anonymize-dates` (and reuse `OverwriteMode` semantics of `bids-inject`)

### Input discovery
- [ ] Resolve `PATHS` to `_scans.tsv` files (reuse / extract the `bids-inject` walker)
- [ ] Select media rows (`ScanRecordKind.is_reprostim_media`), apply `--match` and `--ignore-path`
- [ ] Resolve and validate the media file of each row (missing → row error)

### QR records
- [ ] Load `*.qrinfo.jsonl` (`ParseSummary` + `QrRecord`) with validation
- [ ] `parse` mode: run `qr-parse` on the injected media
- [ ] `embed-existing` / `auto`: locate cached JSONL; re-base per-source records to the clip window
      using `reprostim_offset` and the clip duration (if per-source JSONL is chosen)
- [ ] Trigger detection: first record with `data.event == "trigger"` (`EventType.MRI_TRIGGER_RECEIVED`)

### Outputs
- [ ] A) `_scans.tsv` media-row columns: `qr_count`, `qr_first_trigger_offset`,
      `qr_first_trigger_abstime`, `reprostim_isotime_full`, `reprostim_isotime_offset`,
      `video_duration`, `video_framecount`; idempotent insert-or-update, existing columns untouched
- [ ] B) `_events.tsv`: `onset`, `duration`, `trial_type=qr`, `isotime_start`, `isotime_end`,
      `frame_start`, `frame_end`, `data` (JSON string, tabs/newlines escaped), sorted by `onset`
- [ ] Empty (header-only) `_events.tsv` when no QR codes found; `qr_count = 0`
- [ ] C) `events.json` asset (`src/reprostim/assets/bids/events.json`): column descriptions,
      `trial_type` level `qr`
- [ ] C) HED tags for the QR stimulus (annotation tool → manual review → HED validation)
- [ ] D) extend `assets/bids/scans.json` with the seven new columns
- [ ] Overwrite policy (`skip|force|always|error`) for `_events.tsv`/`_events.json`
- [ ] Dry-run: report planned changes, write nothing
- [ ] Atomic write of `_scans.tsv`

### Date anonymization
- [ ] `strip`: drop date, keep time of day (placeholder date)
- [ ] `none`: unchanged
- [ ] `offset`: subtract `--date-offset` days
- [ ] Apply to `qr_first_trigger_abstime`, `reprostim_isotime_*`, `isotime_start/end`, and dates in `data`
- [ ] Relative values (`onset`, `duration`, `*_offset`, `video_*`) never modified
- [ ] Cross-check with bids-utils issue #10 for consistency

### Reporting / errors
- [ ] Per-row errors don't stop the batch; summary line `N processed, M written, K errors`;
      non-zero exit on any error
- [ ] Fatal pre-checks: `offset` without `--date-offset`, missing dataset directory

## Config file support

- [ ] `BidsQrInjectConfig` class + `bids_qr_inject` root slot in `config.linkml.yaml`
      (snake_case names), replacing nothing (new command, no existing stub)
- [ ] `make generate-config`, `isort`/`black` on `config_model.py`, commit generated files
- [ ] Tests for the new config section in `tests/cli/test_entrypoint.py`; update
      `.ai/cli/config-spec.md` / `config-tasks.md`

## Tests

- [ ] `tests/bids/test_qr_inject.py`: QR loading, trigger detection, re-basing, `_scans.tsv`
      columns, `_events.tsv` content, idempotent re-run, overwrite policies, dry-run, errors
- [ ] Anonymization: `strip`/`none`/`offset`, dates inside `data`, option validation
- [ ] Click options layer via `CliRunner` (defaults, choices, required combinations, exit codes)
- [ ] Small fixture data under `tests/data/` (tiny `.qrinfo.jsonl` + `_scans.tsv`; no large videos)
- [ ] Target 100% statement/branch coverage of `bids/qr_inject.py` and `cli/cmd_bids_qr_inject.py`
      (as for `bids-inject-sidecar`)

## Future Work

- [ ] `bids-qr-sync` (issue #14): use the written columns to refine alignment
- [ ] BIRCH device events as a separate future `_events` output
- [ ] Optional mapping of selected `data` keys (acquisition/series numbers, keys, audio data) to
      dedicated `_events.tsv` columns (skipped for now per the issue)
- [ ] Dropping `--buffer-before/after` when QR sync proves exact (issue #275)
