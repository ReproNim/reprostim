#!/bin/bash

set -eu

thisdir=$(dirname "$0")

echo "Building containers for ReproStim.."

cd ../../containers/repronim-reprostim
pwd

echo execute generate_container.sh
./generate_container.sh

echo execute build_singularity.sh
./build_singularity.sh
