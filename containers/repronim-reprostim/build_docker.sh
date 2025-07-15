#!/bin/bash

set -eu


REPROSTIM_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
REPROSTIM_SUFFIX_NOTAG=repronim-reprostim
REPROSTIM_SUFFIX=${REPROSTIM_SUFFIX_NOTAG}-${REPROSTIM_VERSION}

(
  set -e
  trap 'echo "[-] Docker build failed"; exit 1' ERR

  cd ../../..
  echo "$PWD"

  echo "Building docker container '${REPROSTIM_SUFFIX}' for ReproStim v${REPROSTIM_VERSION}.."
  #
  docker build -f ./reprostim/containers/repronim-reprostim/Dockerfile.${REPROSTIM_SUFFIX_NOTAG} \
    -t repronim/reprostim:${REPROSTIM_VERSION} \
    -t repronim/reprostim:latest \
    .
)
echo "Done."
