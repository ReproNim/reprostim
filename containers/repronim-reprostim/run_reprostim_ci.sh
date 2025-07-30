#!/bin/bash

#
# This script is test script to run Singularity or Docker container
# with the latest git tag version of ReproStim
#

REPROSTIM_CONTAINER_TYPE="${REPROSTIM_CONTAINER_TYPE:-singularity}"

export REPROSTIM_PATH="$(cd "$(dirname "$0")/.." && pwd)"


REPROSTIM_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.1")
# REPROSTIM_OVERLAY=--overlay ./repronim-reprostim-${REPROSTIM_VERSION}.overlay
REPROSTIM_OVERLAY=
if [[ "$REPROSTIM_CONTAINER_TYPE" == "docker" ]]; then
  REPROSTIM_CONTAINER_IMAGE="repronim/reprostim:${REPROSTIM_VERSION}"
  DOCKER_TTY=""
  if [ -t 1 ]; then
    DOCKER_TTY="-t"
  fi
elif [[ "$REPROSTIM_CONTAINER_TYPE" == "singularity" ]]; then
  REPROSTIM_CONTAINER_IMAGE="./repronim-reprostim-${REPROSTIM_VERSION}.sing"
fi


log() {
  if [[ "${REPROSTIM_QUIET:-0}" == "0" ]]; then
    echo "$@"
  fi
}

log "Run ReproStim ${REPROSTIM_CONTAINER_TYPE} CI/CD Container v${REPROSTIM_VERSION}.."
log "  [REPROSTIM_PATH] : ${REPROSTIM_PATH}"
log "  [IMAGE]          : ${REPROSTIM_CONTAINER_IMAGE}"
log "  [OVERLAY]        : ${REPROSTIM_OVERLAY}"
log "  [ARGS]           : $@"


if [[ "$REPROSTIM_CONTAINER_TYPE" == "docker" ]]; then
  docker run --rm -i ${DOCKER_TTY} \
    -v "${REPROSTIM_PATH}:${REPROSTIM_PATH}" \
    -w "${REPROSTIM_PATH}" \
    --env DISPLAY=$DISPLAY \
    ${REPROSTIM_OVERLAY} ${REPROSTIM_CONTAINER_IMAGE} \
    -m reprostim $@
elif [[ "$REPROSTIM_CONTAINER_TYPE" == "singularity" ]]; then
  singularity exec \
    --cleanenv --contain \
    -B ${TMPDIR:-/tmp} \
    -B ${REPROSTIM_PATH} \
    --env DISPLAY=$DISPLAY \
    ${REPROSTIM_OVERLAY} ${REPROSTIM_CONTAINER_IMAGE} \
    python3 -m reprostim $@
else
  log "Unknown REPROSTIM_CONTAINER_TYPE: ${REPROSTIM_CONTAINER_TYPE}"
  exit 1
fi