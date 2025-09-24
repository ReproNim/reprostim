#!/bin/bash

set -eu

thisdir=$(dirname "$0")

echo "Test CI/CD containers for ReproStim.."

cd ${thisdir}
echo Test reprostim --version
export REPROSTIM_CONTAINER_RUN_MODE="reprostim"
./run_reprostim_container.sh --version

cd ${thisdir}
echo Test reprostim --help
export REPROSTIM_CONTAINER_RUN_MODE="reprostim"
./run_reprostim_container.sh --help

cd ${thisdir}
echo Test reprostim-videocapture --help
export REPROSTIM_CONTAINER_RUN_MODE="reprostim-videocapture"
./run_reprostim_container.sh --help
