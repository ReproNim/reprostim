#!/bin/bash
# shellcheck disable=SC2086

#
# This script is test script to run Singularity or Docker container
# with the latest git tag version of ReproStim
#

REPROSTIM_CONTAINER_TYPE="${REPROSTIM_CONTAINER_TYPE:-singularity}"
REPROSTIM_CONTAINER_RUN_MODE="${REPROSTIM_CONTAINER_RUN_MODE:-reprostim}"

REPROSTIM_PATH="$(cd "$(dirname "$0")/.." && pwd)"
export REPROSTIM_PATH


REPROSTIM_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.1")
# REPROSTIM_OVERLAY=--overlay ./repronim-reprostim-${REPROSTIM_VERSION}.overlay
REPROSTIM_OVERLAY=
if [[ "$REPROSTIM_CONTAINER_TYPE" == "docker" ]]; then
  REPROSTIM_CONTAINER_IMAGE="${REPROSTIM_CONTAINER_IMAGE:-repronim/reprostim:${REPROSTIM_VERSION}}"
  DOCKER_TTY=""
  if [ -t 1 ]; then
    DOCKER_TTY="-t"
  fi
elif [[ "$REPROSTIM_CONTAINER_TYPE" == "singularity" ]]; then
  REPROSTIM_CONTAINER_IMAGE="${REPROSTIM_CONTAINER_IMAGE:-./repronim-reprostim-${REPROSTIM_VERSION}.sing}"
fi

# Calculate entry point and command to run inside container
REPROSTIM_RUN_RAW_MODES=(python reprostim-videocapture psychopy ffmpeg ffprobe v4l2-ctl mediainfo parallel rsync py-spy)
REPROSTIM_CONTAINER_ENTRYPOINT=""
if [[ " ${REPROSTIM_RUN_RAW_MODES[*]} " == *" $REPROSTIM_CONTAINER_RUN_MODE "* ]]; then
    REPROSTIM_CONTAINER_APP="$REPROSTIM_CONTAINER_RUN_MODE"
    # clear/remove python entrypoint for standalone apps
    if [ "$REPROSTIM_CONTAINER_TYPE" = "docker" ]; then
        REPROSTIM_CONTAINER_ENTRYPOINT="--entrypoint="
    fi

    # provide custom python module run command for singularity and docker
    if [ "$REPROSTIM_CONTAINER_RUN_MODE" = "python" ]; then
        REPROSTIM_CONTAINER_ENTRYPOINT=""
        if [ "$REPROSTIM_CONTAINER_TYPE" = "docker" ]; then
            REPROSTIM_CONTAINER_APP=""
        elif [ "$REPROSTIM_CONTAINER_TYPE" = "singularity" ]; then
            REPROSTIM_CONTAINER_APP="python3"
        fi
    fi

elif [ "$REPROSTIM_CONTAINER_TYPE" = "docker" ]; then
    REPROSTIM_CONTAINER_APP="-m reprostim"
elif [ "$REPROSTIM_CONTAINER_TYPE" = "singularity" ]; then
    REPROSTIM_CONTAINER_APP="python3 -m reprostim"
else
    REPROSTIM_CONTAINER_APP="-m reprostim"
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
log "  [ARGS]           : $*"

#
# Prepare XAUTHORITY path (fallback to $HOME/.Xauthority)
# also before running docker container with psychopy UI allow
# access to X server with:
#
#  xhost +local:root
#    or
#  xhost +local:docker
#
# and optionally to quiet Podman (when "Emulate Docker CLI" listed in logs):
#  sudo touch /etc/containers/nodocker
#
XAUTHORITY_HOST="${XAUTHORITY:-$HOME/.Xauthority}"

if [[ "$REPROSTIM_CONTAINER_TYPE" == "docker" ]]; then
  docker run --rm -i ${DOCKER_TTY} \
    ${REPROSTIM_CONTAINER_ENTRYPOINT} \
    -v "${REPROSTIM_PATH}:${REPROSTIM_PATH}" \
    -w "${REPROSTIM_PATH}" \
    --env DISPLAY=$DISPLAY \
    -v "${XAUTHORITY_HOST}:${XAUTHORITY_HOST}:ro" \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    ${REPROSTIM_OVERLAY} ${REPROSTIM_CONTAINER_IMAGE} \
    ${REPROSTIM_CONTAINER_APP} "$@"
elif [[ "$REPROSTIM_CONTAINER_TYPE" == "singularity" ]]; then
  singularity exec \
    --cleanenv --contain \
    -B ${TMPDIR:-/tmp} \
    -B ${REPROSTIM_PATH} \
    --env DISPLAY=$DISPLAY \
    ${REPROSTIM_OVERLAY} ${REPROSTIM_CONTAINER_IMAGE} \
    ${REPROSTIM_CONTAINER_APP} "$@"
else
  log "Unknown REPROSTIM_CONTAINER_TYPE: ${REPROSTIM_CONTAINER_TYPE}"
  exit 1
fi
