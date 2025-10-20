#!/bin/bash
# shellcheck disable=SC2086

set -eu

thisdir=$(dirname "$0")

PYTHON_VERSION=3.10

PSYCHOPY_VERSION=2025.2.0
PSYCHOPY_INSTALL_DIR=/opt/psychopy
PSYCHOPY_VENV_NAME=psychopy_${PSYCHOPY_VERSION}_py${PYTHON_VERSION}
PSYCHOPY_HOME=${PSYCHOPY_INSTALL_DIR}/${PSYCHOPY_VENV_NAME}
PSYCHOPY_VENV_BIN=${PSYCHOPY_HOME}/.venv/bin

REPROSTIM_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.1")
# Decided to go without version to make diff easier to analyze etc
REPROSTIM_SUFFIX=repronim-reprostim # -${REPROSTIM_VERSION}
REPROSTIM_GIT_HOME=$(git rev-parse --show-toplevel)
REPROSTIM_HOME=/opt/reprostim
REPROSTIM_CAPTURE_ENABLED="${REPROSTIM_CAPTURE_ENABLED:-0}"
REPROSTIM_CAPTURE_PACKAGES_DEV=""
REPROSTIM_CAPTURE_PACKAGES_RUNTIME=""
REPROSTIM_CAPTURE_BUILD="echo 'ReproStim capture build is disabled'"
REPROSTIM_CAPTURE_CLEAN="echo 'ReproStim capture clean is disabled'"

if [[ "$REPROSTIM_CAPTURE_ENABLED" == "1" ]]; then
  REPROSTIM_CAPTURE_PACKAGES_DEV="libyaml-cpp-dev libspdlog-dev catch2 libv4l-dev libudev-dev libopencv-dev libcurl4-openssl-dev nlohmann-json3-dev cmake g++"
  REPROSTIM_CAPTURE_PACKAGES_RUNTIME="libyaml-cpp0.7 libfmt9"
  REPROSTIM_CAPTURE_BUILD="cd \"$REPROSTIM_HOME/src/reprostim-capture\"; mkdir build; cd build; cmake ..; make; cd ..; cmake --install build; rm -rf \"$REPROSTIM_HOME/src/reprostim-capture/build\"; reprostim-videocapture -V"
  REPROSTIM_CAPTURE_CLEAN="apt-get remove --purge -y $REPROSTIM_CAPTURE_PACKAGES_DEV && apt-get autoremove -y"
  # Extend with packages hold if runtime packages env exist
  if [[ -n "$REPROSTIM_CAPTURE_PACKAGES_RUNTIME" ]]; then
      REPROSTIM_CAPTURE_CLEAN="apt-mark manual $REPROSTIM_CAPTURE_PACKAGES_RUNTIME && apt-mark hold $REPROSTIM_CAPTURE_PACKAGES_RUNTIME && $REPROSTIM_CAPTURE_CLEAN"
  fi
fi


MODE=${1:-default}


if [[ "$MODE" == "ci" ]]; then
  echo "Running in CI/CD mode, install reprostim from current worktree"
  REPROSTIM_COPY="${REPROSTIM_GIT_HOME} ${REPROSTIM_HOME}"
  REPROSTIM_RUN_INSTALL="${PSYCHOPY_VENV_BIN}/pip install ${REPROSTIM_HOME}[all,disp_mon]"
else
  echo "Running in default mode, install reprostim from PyPI"
  REPROSTIM_COPY=""
  REPROSTIM_RUN_INSTALL="${PSYCHOPY_VENV_BIN}/pip install reprostim[all,disp_mon]==${REPROSTIM_VERSION}"
fi



generate() {
  if [[ "$1" == docker && "$MODE" == "ci" ]]; then
    REPROSTIM_COPY="reprostim ${REPROSTIM_HOME}"
  fi

  if [[ "$1" == singularity && "$MODE" == "ci" ]]; then
    REPROSTIM_COPY="${REPROSTIM_GIT_HOME} ${REPROSTIM_HOME}"
  fi

  if [[ -n "${REPROSTIM_COPY:-}" ]]; then
    REPROSTIM_COPY_ARG="--copy ${REPROSTIM_COPY}"
  else
    REPROSTIM_COPY_ARG=""
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
          libgtk-3-dev libwxgtk3.2-dev libwxgtk-media3.2-dev libwxgtk-webview3.2-dev libcanberra-gtk3-module \
          libusb-1.0-0-dev portaudio19-dev libasound2-dev pulseaudio pavucontrol pulseaudio-utils \
          vim wget strace time ncdu gnupg curl procps pigz less tree python3 python3-pip \
          "${REPROSTIM_CAPTURE_PACKAGES_RUNTIME}" \
          "${REPROSTIM_CAPTURE_PACKAGES_DEV}" \
    --run "git clone https://github.com/wieluk/psychopy_linux_installer/ /opt/psychopy-installer; cd /opt/psychopy-installer; git checkout tags/v2.2.4" \
    --run "/opt/psychopy-installer/psychopy_linux_installer --install-dir=${PSYCHOPY_INSTALL_DIR} --venv-name=${PSYCHOPY_VENV_NAME} --psychopy-version=${PSYCHOPY_VERSION} --additional-packages=psychopy_bids==2025.1.2,psychopy-mri-emulator==0.0.2 --python-version=${PYTHON_VERSION} --wxpython-version=4.2.3 -v -f" \
    ${REPROSTIM_COPY_ARG} \
    --run "${REPROSTIM_RUN_INSTALL}" \
    --run "bash -c 'ln -s ${PSYCHOPY_HOME}/start_psychopy /usr/local/bin/psychopy'" \
    --run "bash -c 'b=\$(ls ${PSYCHOPY_VENV_BIN}/python3); echo -e \"#!/bin/sh\n\$b \\\"\\\$@\\\"\" >| /usr/local/bin/python3; chmod a+x /usr/local/bin/python3'" \
    --entrypoint python3 \
    --run "bash -c '$REPROSTIM_CAPTURE_BUILD'" \
    --run "bash -c '$REPROSTIM_CAPTURE_CLEAN'" \
    --run "chmod a+rX -R /opt"
#    --user=reproin \
}

echo "Generating containers for Python v${PYTHON_VERSION} + PsychoPy v${PSYCHOPY_VERSION} + ReproStim v${REPROSTIM_VERSION}.."
#
echo "Dockerfile.${REPROSTIM_SUFFIX} ..."
generate docker > "$thisdir"/Dockerfile.${REPROSTIM_SUFFIX}

echo "Singularity.${REPROSTIM_SUFFIX} ..."
generate singularity > "$thisdir"/Singularity.${REPROSTIM_SUFFIX}
