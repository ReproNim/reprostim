#!/bin/bash

set -eu


REPROSTIM_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
REPROSTIM_SUFFIX_NOTAG=repronim-reprostim
REPROSTIM_SUFFIX=${REPROSTIM_SUFFIX_NOTAG}-${REPROSTIM_VERSION}
TAGS=${REPROSTIM_DOCKER_TAGS:-unstable}


(
  set -e
  trap 'echo "[-] Docker build failed"; exit 1' ERR

  cd ../../..
  echo "$PWD"

  # Construct multiple -t options
  TAG_ARGS=""
  for TAG in $TAGS; do
    TAG_ARGS+=" -t repronim/reprostim:$TAG"
  done

  echo "Building docker container '${REPROSTIM_SUFFIX}' for ReproStim v${REPROSTIM_VERSION}.."
  echo "Using tags: ${TAGS}"
  echo "Using tag args: ${TAG_ARGS}"

  #
  # shellcheck disable=SC2086
  docker build -f ./reprostim/containers/repronim-reprostim/Dockerfile.${REPROSTIM_SUFFIX_NOTAG} \
    $TAG_ARGS \
    .
)
echo "Done."
