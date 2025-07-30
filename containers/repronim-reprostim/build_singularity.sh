#!/bin/bash

set -eu

REPROSTIM_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
REPROSTIM_SUFFIX_NOTAG=repronim-reprostim
REPROSTIM_SUFFIX=${REPROSTIM_SUFFIX_NOTAG}-${REPROSTIM_VERSION}


echo "Building singularity container '${REPROSTIM_SUFFIX}.sing' for ReproStim v${REPROSTIM_VERSION}.."
#
singularity build --fakeroot ${REPROSTIM_SUFFIX}.sing Singularity.${REPROSTIM_SUFFIX_NOTAG}
