#!/bin/bash

set -eu

thisdir=$(dirname "$0")

# Script to build and push Docker images as part of the release process
# This is called from .autorc during `auto shipit`

echo "=== Building and Pushing ReproStim Release Docker Images ==="

# Get the version from git tags
REPROSTIM_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
echo "REPROSTIM_VERSION: $REPROSTIM_VERSION"

# Enable capture in the build
export REPROSTIM_CAPTURE_ENABLED=1

# Specify tags for the docker image: master, latest, and the version tag
export REPROSTIM_DOCKER_TAGS="master latest $REPROSTIM_VERSION"
echo "Docker tags to build: $REPROSTIM_DOCKER_TAGS"

# Build the Docker image
echo ""
echo "--- Building ReproStim Docker image ---"
cd "$thisdir"
./build_reprostim_container.sh docker

# Push the Docker image
echo ""
echo "--- Pushing release ReproStim docker image with version: $REPROSTIM_VERSION ---"
if [ -z "${DOCKER_LOGIN:-}" ] || [ -z "${DOCKER_TOKEN:-}" ]; then
  echo "ERROR: DOCKER_LOGIN and DOCKER_TOKEN environment variables must be set"
  exit 1
fi

docker login -u "$DOCKER_LOGIN" --password-stdin <<<"$DOCKER_TOKEN"
docker push --all-tags repronim/reprostim

echo ""
echo "=== Successfully built and pushed Docker images ==="
echo "Tags pushed: $REPROSTIM_DOCKER_TAGS"