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

- [ ] **`generate_container.sh`**: Change `--entrypoint python3` to `--entrypoint reprostim`
  so both Docker and Singularity images use `reprostim` as their default entrypoint.

- [ ] **`run_reprostim.sh`**: Change `python3 -m reprostim "$@"` to `reprostim "$@"` in the
  `singularity exec` call.

- [ ] **`run_reprostim_ci.sh`**: Add `reprostim` to the `REPROSTIM_RUN_RAW_MODES` array so it
  is treated as a direct binary (Docker gets `--entrypoint=` override + `reprostim` as app;
  Singularity exec gets `reprostim` as command).

- [ ] **`run_reprostim_ci.sh`**: Fix `python` mode for Docker — the current code resets
  `REPROSTIM_CONTAINER_ENTRYPOINT=""` relying on the old `python3` default entrypoint.
  After the change the default is `reprostim`, so set
  `REPROSTIM_CONTAINER_ENTRYPOINT="--entrypoint=python3"` explicitly for Docker `python` mode.

- [ ] **`run_reprostim_ci.sh`**: Update the fallback `else` branch (previously handled
  `reprostim` mode via `python3 -m reprostim`) to use `reprostim` directly, since that case
  is now dead code for known modes.

- [ ] **Verify** GitHub Actions workflow (`docker.yml`) — `test_reprostim_container.sh` already
  uses `REPROSTIM_CONTAINER_RUN_MODE="reprostim"` which will route through the updated
  `REPROSTIM_RUN_RAW_MODES` path; confirm no workflow-level changes are needed after above fixes.
