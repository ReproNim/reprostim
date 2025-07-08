#!/bin/bash

#
# This script is test script to run Singularity container
# with the latest git tag version of ReproStim
#

export REPROSTIM_PATH="$(cd "$(dirname "$0")/.." && pwd)"


REPROSTIM_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.1")
# REPROSTIM_OVERLAY=--overlay ./repronim-reprostim-${REPROSTIM_VERSION}.overlay
REPROSTIM_OVERLAY=
REPROSTIM_CONTAINER=./repronim-reprostim-${REPROSTIM_VERSION}.sing

echo "Run ReproStim Singularity CI/CD Container v${REPROSTIM_VERSION}.."
echo "  [REPROSTIM_PATH] : ${REPROSTIM_PATH}"
echo "  [CONTAINER]      : ${SINGULARITY_CONTAINER}"
echo "  [OVERLAY]        : ${REPROSTIM_OVERLAY}"
echo "  [ARGS]           : $@"


singularity exec \
  --cleanenv --contain \
  -B ${TMPDIR:-/tmp} \
  -B ${REPROSTIM_PATH} \
  --env DISPLAY=$DISPLAY \
  ${REPROSTIM_OVERLAY} ${REPROSTIM_CONTAINER} \
  python3 -m reprostim $@
