#!/bin/bash

set -eu

# thisdir=$(dirname "$0")

log() {
  if [[ "${REPROSTIM_QUIET:-0}" == "0" ]]; then
    echo "$@"
  fi
}

log "Run CI/CD containers for ReproStim.."

cd ../../containers/repronim-reprostim
# pwd

log "Execute run_reprostim_ci.sh"
./run_reprostim_ci.sh $@
