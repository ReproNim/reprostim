#!/bin/bash

set -eu

thisdir=$(dirname "$0")

echo "Building containers for ReproStim.."

cd ../../containers/repronim-reprostim
pwd

echo Execute generate_container.sh
./generate_container.sh ci

ls -l

echo Execute build_singularity.sh
./build_singularity.sh

ls -l
