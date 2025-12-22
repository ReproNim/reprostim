#!/bin/bash

set -eu

thisdir=$(dirname "$0")

echo "Test CI/CD containers for ReproStim.."

cd "${thisdir}"
echo Test reprostim --version
export REPROSTIM_CONTAINER_RUN_MODE="reprostim"
./run_reprostim_container.sh --version

cd "${thisdir}"
echo Test reprostim --help
export REPROSTIM_CONTAINER_RUN_MODE="reprostim"
./run_reprostim_container.sh --help

cd "${thisdir}"
echo Test reprostim-videocapture --help
export REPROSTIM_CONTAINER_RUN_MODE="reprostim-videocapture"
./run_reprostim_container.sh --help

cd "${thisdir}"
echo Test ffmpeg -version
export REPROSTIM_CONTAINER_RUN_MODE="ffmpeg"
./run_reprostim_container.sh -version

cd "${thisdir}"
echo Test ffprobe -version
export REPROSTIM_CONTAINER_RUN_MODE="ffprobe"
./run_reprostim_container.sh -version

cd "${thisdir}"
echo Test v4l2-ctl --version
export REPROSTIM_CONTAINER_RUN_MODE="v4l2-ctl"
./run_reprostim_container.sh --version

cd "${thisdir}"
echo Test mediainfo --version
export REPROSTIM_CONTAINER_RUN_MODE="mediainfo"
./run_reprostim_container.sh --version

cd "${thisdir}"
echo Test parallel --version
export REPROSTIM_CONTAINER_RUN_MODE="parallel"
./run_reprostim_container.sh --version

cd "${thisdir}"
echo Test rsync --version
export REPROSTIM_CONTAINER_RUN_MODE="rsync"
./run_reprostim_container.sh --version

cd "${thisdir}"
echo Test Python visidata --version
export REPROSTIM_CONTAINER_RUN_MODE="python"
./run_reprostim_container.sh -m visidata --version

# cd "${thisdir}"
# echo Test Python con-duct --version
# export REPROSTIM_CONTAINER_RUN_MODE="python"
# ./run_reprostim_container.sh -m con-duct --version