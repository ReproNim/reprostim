#!/bin/bash

set -eu

# thisdir=$(dirname "$0")

print_help() {
  cat <<EOF
Usage: $0 [TARGET]

Build repronim-reprostim containers for ReproStim.

Arguments:
  TARGET         Build target: "singularity" (default) or "docker"

Options:
  -h, --help     Show this help message and exit

Examples:
  $0                # build singularity container (default)
  $0 docker         # build docker container
EOF
}

# Parse arguments
target="${1:-singularity}"
target=$(echo "$target" | tr '[:upper:]' '[:lower:]') # Convert to lowercase

if [[ "$target" == "-h" || "$target" == "--help" ]]; then
  print_help
  exit 0
fi

if [[ "$target" != "singularity" && "$target" != "docker" ]]; then
  echo "Error: Unknown target '$target'"
  echo "Use --help for usage."
  exit 1
fi

echo "Building containers for ReproStim.."

cd ../../containers/repronim-reprostim
pwd

echo Execute generate_container.sh
./generate_container.sh ci

ls -l


if [[ "$target" == "singularity" ]]; then
  echo Execute build_singularity.sh
  ./build_singularity.sh
elif [[ "$target" == "docker" ]]; then
  echo "Execute build_docker.sh"
  ./build_docker.sh
fi

ls -l
