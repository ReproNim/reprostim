# `repronim-reprostim` Container Task List

Tracks implementation tasks related to `repronim-reprostim` container configuration and scripts.

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
