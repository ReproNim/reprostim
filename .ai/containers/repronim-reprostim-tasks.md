# `repronim-reprostim` Container Task List

Tracks implementation tasks related to `repronim-reprostim` container configuration and scripts.

---

## Add `bids-validator` (via `bids-validator-deno` PyPI package) to container

**Goal**: Make the [bids-standard/bids-validator](https://github.com/bids-standard/bids-validator)
CLI available inside the `repronim-reprostim` container as a raw run mode, same as `rsync`,
`parallel`, `mediainfo`, etc.

**Approach**: Rather than an `apt`/native install, use the precompiled
[`bids-validator-deno`](https://pypi.org/project/bids-validator-deno/) PyPI wheel (pinned to
`3.0.1`). It has no OS-level dependency — its `deno>=2.5.0` requirement resolves to a
platform-specific `deno` wheel (bundling a real Deno binary for linux amd64), so `pip install`
inside the PsychoPy venv is sufficient; no `generate_container.sh` apt package list changes were
needed. Its console-script entry point (`bids-validator-deno`) is not runnable via
`python3 -m bids_validator_deno` (no `__main__.py`), so it needs its own `/usr/local/bin` wrapper,
mirroring the existing `reprostim` wrapper, rather than following the `python -m visidata` pattern.

**Affected files**:
- `containers/repronim-reprostim/setup_container.sh`
- `containers/repronim-reprostim/run_reprostim_ci.sh`
- `tools/ci/test_reprostim_container.sh`

### Tasks

- [x] **`setup_container.sh`**: `pip install --no-cache-dir bids-validator-deno==3.0.1` into the
  PsychoPy venv, alongside `visidata`/`py-spy`.
- [x] **`setup_container.sh`**: Add a `/usr/local/bin/bids-validator-deno` wrapper script
  (`#!/bin/sh` + exec venv binary), same pattern as the `reprostim` wrapper.
- [x] **`run_reprostim_ci.sh`**: Add `bids-validator-deno` to `REPROSTIM_RUN_RAW_MODES` so
  `REPROSTIM_CONTAINER_RUN_MODE=bids-validator-deno` runs it directly (Docker: cleared
  entrypoint; Singularity: `singularity exec ... bids-validator-deno`).
- [x] **`tools/ci/test_reprostim_container.sh`**: Add a `bids-validator-deno --version` smoke
  test, following the `rsync`/`parallel` test blocks.
- [ ] **Regenerate and manually verify** `Dockerfile.repronim-reprostim` /
  `Singularity.repronim-reprostim` via `generate_container.sh`, build the image, and confirm
  `bids-validator-deno --version` and an actual dataset validation run (e.g.
  `bids-validator-deno /data/some-bids-dataset`) both work — not yet run against a real build.
- [ ] Consider documenting the new tool in `containers/repronim-reprostim/README.md` /
  `DOCKERHUB.md` if/when a "bundled tools" list is added there (none currently exists).

---

## [Issue #217](https://github.com/ReproNim/reprostim/issues/217): Make `reprostim` the default container entrypoint

**Goal**: `singularity run <container.sif> <args>` (and `docker run <image> <args>`) should
invoke `reprostim <args>` directly, without requiring explicit `python3 -m reprostim` invocation.

**Affected files**:
- `containers/repronim-reprostim/setup_container.sh`
- `containers/repronim-reprostim/generate_container.sh`
- `containers/repronim-reprostim/run_reprostim.sh`
- `containers/repronim-reprostim/run_reprostim_ci.sh`
- `.github/workflows/docker.yml` (verify no changes needed)

### Tasks

- [x] **`setup_container.sh`**: Extend `PATH` to include `${PSYCHOPY_VENV_BIN}` (e.g. append to
  `/etc/environment` or write a profile script under `/etc/profile.d/`) so that `reprostim` and
  other venv binaries are accessible system-wide without individual wrappers.

- [x] **`setup_container.sh`**: Add `/usr/local/bin/reprostim` wrapper script after the existing
  `python3` wrapper (same pattern: write a one-line `#!/bin/sh` wrapper pointing to
  `${PSYCHOPY_VENV_BIN}/reprostim`).

- [x] **`generate_container.sh`**: Change `--entrypoint python3` to `--entrypoint reprostim`
  so both Docker and Singularity images use `reprostim` as their default entrypoint.

- [x] **`run_reprostim.sh`**: Switch from `singularity exec ... python3 -m reprostim "$@"` to
  `singularity run ... "$@"` — the entrypoint handles `reprostim` invocation automatically.

- [x] **`run_reprostim_ci.sh`**: Update the `else` branch — `reprostim` is the default entrypoint
  so it does not belong in `REPROSTIM_RUN_RAW_MODES`. For Docker set `REPROSTIM_CONTAINER_APP=""`
  (use default entrypoint); for Singularity set `REPROSTIM_CONTAINER_APP="reprostim"` (explicit
  command for `singularity exec`).

- [x] **`run_reprostim_ci.sh`**: Fix `python` mode for Docker — the current code resets
  `REPROSTIM_CONTAINER_ENTRYPOINT=""` relying on the old `python3` default entrypoint.
  After the change the default is `reprostim`, so set
  `REPROSTIM_CONTAINER_ENTRYPOINT="--entrypoint=python3"` explicitly for Docker `python` mode.

- [x] **`run_reprostim_ci.sh`**: Update the fallback `else` branch (previously handled
  `reprostim` mode via `python3 -m reprostim`) to use `reprostim` directly, since that case
  is now dead code for known modes.

- [x] **Verify** GitHub Actions workflow (`docker.yml`) — `test_reprostim_container.sh` already
  uses `REPROSTIM_CONTAINER_RUN_MODE="reprostim"` which will route through the updated
  `else` branch; confirm no workflow-level changes are needed after above fixes.

- [x] **`docs/source/install/install.md`**: Update the example `singularity exec` snippet —
  replace `python3 -m reprostim` with `reprostim` directly.

- [x] **`docs/source/notes/automated-setup.rst`**: Update the example script snippet —
  replace full venv path `/opt/psychopy/.../bin/reprostim` with just `reprostim`.

- [x] **`containers/repronim-reprostim/DOCKERHUB.md`**: Replace `python3 -m reprostim` with
  direct args — Docker entrypoint is now `reprostim`, so `docker run image python3 -m reprostim
  --version` becomes `docker run image --version`.

- [x] **`containers/repronim-reprostim/README.md`**: Replace all `python3 -m reprostim` with
  `reprostim` in `singularity exec` examples (3 occurrences).
