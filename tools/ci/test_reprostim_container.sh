#!/bin/bash

set -eu

thisdir=$(dirname "$0")

echo "Test CI/CD containers for ReproStim.."

cd ${thisdir}
echo Test reprostim --version
./run_reprostim_container.sh --version

cd ${thisdir}
echo Test reprostim --help
./run_reprostim_container.sh --help
