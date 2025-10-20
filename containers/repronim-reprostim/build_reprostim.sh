#!/bin/bash
# shellcheck disable=SC2086,SC2034

set -eu

thisdir=$(dirname "$0")

PYTHON_VERSION=3.10

PSYCHOPY_VERSION=2025.2.0
PSYCHOPY_INSTALL_DIR=/opt/psychopy
PSYCHOPY_VENV_NAME=psychopy_${PSYCHOPY_VERSION}_py${PYTHON_VERSION}
PSYCHOPY_HOME=${PSYCHOPY_INSTALL_DIR}/${PSYCHOPY_VENV_NAME}
PSYCHOPY_VENV_BIN=${PSYCHOPY_HOME}/.venv/bin

# Decided to go without version to make diff easier to analyze etc
REPROSTIM_SUFFIX=repronim-reprostim # -${REPROSTIM_VERSION}
REPROSTIM_HOME=/opt/reprostim
REPROSTIM_CAPTURE_ENABLED="${REPROSTIM_CAPTURE_ENABLED:-0}"
REPROSTIM_CAPTURE_PACKAGES_DEV=""
REPROSTIM_CAPTURE_PACKAGES_RUNTIME=""
REPROSTIM_CAPTURE_BUILD="echo 'ReproStim capture build is disabled'"
REPROSTIM_CAPTURE_CLEAN="echo 'ReproStim capture clean is disabled'"



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



git clone https://github.com/wieluk/psychopy_linux_installer/ /opt/psychopy-installer
cd /opt/psychopy-installer; git checkout tags/v2.2.3

/opt/psychopy-installer/psychopy_linux_installer --install-dir=${PSYCHOPY_INSTALL_DIR} --venv-name=${PSYCHOPY_VENV_NAME} --psychopy-version=${PSYCHOPY_VERSION} --additional-packages=psychopy_bids==2025.1.2,psychopy-mri-emulator==0.0.2 --python-version=${PYTHON_VERSION} --wxpython-version=4.2.3 -v -f
# TODO return REPROSTIM_COPY_ARG}

${REPROSTIM_RUN_INSTALL}
ln -s ${PSYCHOPY_HOME}/start_psychopy /usr/local/bin/psychopy
b=\$(ls ${PSYCHOPY_VENV_BIN}/python3); echo -e \"#!/bin/sh\n\$b \\\"\\\$@\\\"\" >| /usr/local/bin/python3; chmod a+x /usr/local/bin/python3

if [[ "$REPROSTIM_CAPTURE_ENABLED" == "1" ]]; then
  REPROSTIM_CAPTURE_BUILD="cd \"$REPROSTIM_HOME/src/reprostim-capture\"; mkdir build; cd build; cmake ..; make; cd ..; cmake --install build; rm -rf \"$REPROSTIM_HOME/src/reprostim-capture/build\"; reprostim-videocapture -V"
  REPROSTIM_CAPTURE_CLEAN="apt-get remove --purge -y $REPROSTIM_CAPTURE_PACKAGES_DEV && apt-get autoremove -y"
  # Extend with packages hold if runtime packages env exist
  if [[ -n "$REPROSTIM_CAPTURE_PACKAGES_RUNTIME" ]]; then
      REPROSTIM_CAPTURE_CLEAN="apt-mark manual $REPROSTIM_CAPTURE_PACKAGES_RUNTIME && apt-mark hold $REPROSTIM_CAPTURE_PACKAGES_RUNTIME && $REPROSTIM_CAPTURE_CLEAN"
  fi
fi
chmod a+rX -R /opt
