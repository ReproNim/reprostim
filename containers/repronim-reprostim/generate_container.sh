#!/bin/bash
# shellcheck disable=SC2086

set -eu

thisdir=$(dirname "$0")

MODE=${1:-default}

PYTHON_VERSION=3.10
PSYCHOPY_VERSION=2025.2.0
REPROSTIM_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.1")
# Decided to go without version to make diff easier to analyze etc
REPROSTIM_SUFFIX=repronim-reprostim # -${REPROSTIM_VERSION}
REPROSTIM_HOME=/opt/reprostim
REPROSTIM_GIT_HOME=$(git rev-parse --show-toplevel)
REPROSTIM_CI_HOME="${thisdir}/reprostim"
REPROSTIM_CAPTURE_ENABLED="${REPROSTIM_CAPTURE_ENABLED:-0}"
REPROSTIM_CAPTURE_PACKAGES_DEV=""
REPROSTIM_CAPTURE_PACKAGES_RUNTIME="mc"

# include capture packages if enabled, two subsets: dev and runtime
# dev packages are needed only during build time
# runtime packages are needed during runtime and build time
if [[ "$REPROSTIM_CAPTURE_ENABLED" == "1" ]]; then
  REPROSTIM_CAPTURE_PACKAGES_DEV="libyaml-cpp-dev libspdlog-dev catch2 libv4l-dev libudev-dev libopencv-dev libcurl4-openssl-dev nlohmann-json3-dev cmake g++"
  REPROSTIM_CAPTURE_PACKAGES_RUNTIME="mc libyaml-cpp0.7 libfmt9"
fi

generate() {
  # Somehow --copy source differs between docker and singularity
  REPROSTIM_COPY_SRC="${REPROSTIM_GIT_HOME}"
  if [[ "$1" == docker ]]; then
    REPROSTIM_COPY_SRC="reprostim"
  fi

  # copy the setup script to /opt/setup_container.sh
  REPROSTIM_COPY_ARGS=( "--copy" "${REPROSTIM_COPY_SRC}/containers/repronim-reprostim/setup_container.sh" "/opt/setup_container.sh" )

  # optionally copy the current worktree into the container
  # for CI mode to build reprostim package from current code
  # rather than from PyPI
  if [[ "$MODE" == "ci" ]]; then
    # add another --copy pair for CI
    REPROSTIM_COPY_ARGS+=( "--copy" "${REPROSTIM_COPY_SRC}" "${REPROSTIM_HOME}" )
  fi

  # shellcheck disable=SC2034
  [ "$1" == singularity ] && add_entry=' "$@"' || add_entry=''
  ndversion=2.0.0
    # Thought to use conda-forge for this, but feedstock is not maintained:
    #  https://github.com/conda-forge/psychopy-feedstock/issues/64
    #   --miniconda version=py312_24.5.0-0 conda_install="conda-forge::psychopy conda-forge::qrcode" \
    # Had to go with 3.11 due to https://stackoverflow.com/questions/77364550/attributeerror-module-pkgutil-has-no-attribute-impimporter-did-you-mean
    # Need extra -dev libraries etc to install/build wxpython
    # Gave up on native psychopy installation "myself" - decided to use the script!
    # sudo needed for the psychopy-installer script: https://github.com/wieluk/psychopy_linux_installer/issues/11
    # Surprise! cannot just ln -s python3 since then it would not have correct sys.path!
  docker run --rm repronim/neurodocker:$ndversion generate "$1" \
    --base-image=neurodebian:bookworm \
    --pkg-manager=apt \
    --install build-essential pkg-config git \
          sudo \
          libgtk-3-dev libwebkit2gtk-4.1 libwxgtk3.2-dev libwxgtk-media3.2-dev libwxgtk-webview3.2-dev libcanberra-gtk3-module \
          libsdl2-2.0-0 libzbar0 libusb-1.0-0-dev portaudio19-dev libasound2-dev pulseaudio pavucontrol pulseaudio-utils \
          vim wget strace time ncdu gnupg curl procps pigz less tree python3 python3-pip \
          ffmpeg mediainfo v4l-utils \
          "${REPROSTIM_CAPTURE_PACKAGES_RUNTIME}" \
          "${REPROSTIM_CAPTURE_PACKAGES_DEV}" \
    "${REPROSTIM_COPY_ARGS[@]}" \
    --run "bash -c 'chmod a+rX /opt/setup_container.sh && PYTHON_VERSION=\"${PYTHON_VERSION}\" PSYCHOPY_VERSION=\"${PSYCHOPY_VERSION}\" REPROSTIM_VERSION=\"${REPROSTIM_VERSION}\" REPROSTIM_HOME=\"${REPROSTIM_HOME}\" MODE=\"${MODE}\" REPROSTIM_CAPTURE_ENABLED=\"${REPROSTIM_CAPTURE_ENABLED}\" REPROSTIM_CAPTURE_PACKAGES_DEV=\"${REPROSTIM_CAPTURE_PACKAGES_DEV}\" REPROSTIM_CAPTURE_PACKAGES_RUNTIME=\"${REPROSTIM_CAPTURE_PACKAGES_RUNTIME}\" /opt/setup_container.sh'" \
    --entrypoint python3
#    --user=reproin \
}

echo "Generating containers for Python v${PYTHON_VERSION} + PsychoPy v${PSYCHOPY_VERSION} + ReproStim v${REPROSTIM_VERSION}.."
#

if [[ "$MODE" == "ci" ]]; then
  echo "Copy current worktree into container for CI mode: ${REPROSTIM_GIT_HOME} -> ${REPROSTIM_CI_HOME}"
  # delete previous copy if exists
  rm -rf "${REPROSTIM_CI_HOME}"
  mkdir -p "${REPROSTIM_CI_HOME}"
  cp -r "${REPROSTIM_GIT_HOME}"/*.* "${REPROSTIM_CI_HOME}"
  cp -r "${REPROSTIM_GIT_HOME}/.git" "${REPROSTIM_CI_HOME}/.git"
  cp -r "${REPROSTIM_GIT_HOME}/docs" "${REPROSTIM_CI_HOME}/docs"
  mkdir -p "${REPROSTIM_CI_HOME}/containers/repronim-reprostim"
  cp -r "${REPROSTIM_GIT_HOME}/containers/repronim-reprostim/setup_container.sh" "${REPROSTIM_CI_HOME}/containers/repronim-reprostim"
  cp -r "${REPROSTIM_GIT_HOME}/examples" "${REPROSTIM_CI_HOME}/examples"
  cp -r "${REPROSTIM_GIT_HOME}/src" "${REPROSTIM_CI_HOME}/src"
  cp -r "${REPROSTIM_GIT_HOME}/LICENSES" "${REPROSTIM_CI_HOME}/LICENSES"
  cp -r "${REPROSTIM_GIT_HOME}/tests" "${REPROSTIM_CI_HOME}/tests"
  cp -r "${REPROSTIM_GIT_HOME}/tools" "${REPROSTIM_CI_HOME}/tools"
fi

echo "Dockerfile.${REPROSTIM_SUFFIX} ..."
generate docker > "$thisdir"/Dockerfile.${REPROSTIM_SUFFIX}

echo "Singularity.${REPROSTIM_SUFFIX} ..."
generate singularity > "$thisdir"/Singularity.${REPROSTIM_SUFFIX}
