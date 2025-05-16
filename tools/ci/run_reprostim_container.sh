#!/bin/bash

set -eu

thisdir=$(dirname "$0")

echo "Run CI/CD containers for ReproStim.."

cd ../../containers/repronim-reprostim
pwd

echo Execute run_reprostim_ci.sh
./run_reprostim_ci.sh $@
