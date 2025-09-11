#!/bin/bash

set -eu

REPROSTIM_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
REPROSTIM_SUFFIX_NOTAG=repronim-reprostim
REPROSTIM_SUFFIX=${REPROSTIM_SUFFIX_NOTAG}-${REPROSTIM_VERSION}

# Use --fakeroot if not running as root
if [ "$EUID" -eq 0 ]; then
    FAKEROOT_ARG=""
else
    FAKEROOT_ARG="--fakeroot"
fi

echo "Building singularity container '${REPROSTIM_SUFFIX}.sing' for ReproStim v${REPROSTIM_VERSION}.."
#
singularity build $FAKEROOT_ARG "${REPROSTIM_SUFFIX}.sing" "Singularity.${REPROSTIM_SUFFIX_NOTAG}"
