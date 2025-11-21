#!/bin/bash
# shellcheck disable=SC2086,SC2034

# This is internal script used by Docker/Singularity to setup the container
# and it's automatically copied into the container image under /opt/setup_container.sh
# location. It is not meant to be run directly by users.
#
# Note: env variables passed explicitly from generate_container.sh script:
#   $MODE
#   $PYTHON_VERSION
#   $PSYCHOPY_VERSION
#   $REPROSTIM_VERSION
#   $REPROSTIM_HOME
#   $REPROSTIM_CAPTURE_ENABLED
#   $REPROSTIM_CAPTURE_PACKAGES_DEV
#   $REPROSTIM_CAPTURE_PACKAGES_RUNTIME

set -eu

thisdir=$(dirname "$0")

PSYCHOPY_INSTALL_DIR=/opt/psychopy
PSYCHOPY_VENV_NAME=psychopy_${PSYCHOPY_VERSION}_py${PYTHON_VERSION}
PSYCHOPY_HOME=${PSYCHOPY_INSTALL_DIR}/${PSYCHOPY_VENV_NAME}
PSYCHOPY_VENV_BIN=${PSYCHOPY_HOME}/.venv/bin


# Install psychopy_linux_installer from GitHub
echo "Install psychopy_linux_installer from GitHub..."
git clone --branch v2.2.4 --depth 1 https://github.com/wieluk/psychopy_linux_installer/ /opt/psychopy-installer
cd /opt/psychopy-installer

# Install PsychoPy via psychopy_linux_installer
echo "Install PsychoPy v${PSYCHOPY_VERSION} via psychopy_linux_installer..."
/opt/psychopy-installer/psychopy_linux_installer --install-dir=${PSYCHOPY_INSTALL_DIR} --venv-name=${PSYCHOPY_VENV_NAME} --psychopy-version=${PSYCHOPY_VERSION} --additional-packages=psychopy_bids==2025.1.2,psychopy-mri-emulator==0.0.2 --python-version=${PYTHON_VERSION} --wxpython-version=4.2.3 --cleanup -v -f
# Create symlink to psychopy executable
ln -sf "${PSYCHOPY_HOME}/start_psychopy" /usr/local/bin/psychopy

# Install reprostim package from PyPI or from current worktree in CI mode
if [[ "$MODE" == "ci" ]]; then
  echo "Running in CI/CD mode, install reprostim from current worktree"
  "${PSYCHOPY_VENV_BIN}/pip" install "${REPROSTIM_HOME}[all,disp_mon]"
else
  echo "Running in default mode, install reprostim from PyPI"
  "${PSYCHOPY_VENV_BIN}/pip" install "reprostim[all,disp_mon]==${REPROSTIM_VERSION}"
fi

# Create symlink to python3 in psychopy venv as default python3
echo "Creating symlink to python3 in psychopy venv as default python3"
b=$(ls "${PSYCHOPY_VENV_BIN}/python3")
echo -e "#!/bin/sh\n$b \"\$@\"" >| /usr/local/bin/python3
chmod a+x /usr/local/bin/python3

if [[ "$REPROSTIM_CAPTURE_ENABLED" == "1" ]]; then
  # Build reprostim-capture from source
  echo "Building reprostim-capture from source..."
  cd "${REPROSTIM_HOME}/src/reprostim-capture"
  mkdir build
  cd build
  cmake ..
  make
  cd ..

  # Install the built binary
  echo "Installing reprostim-capture..."
  cmake --install build

  # Clean build files
  rm -rf "${REPROSTIM_HOME}/src/reprostim-capture/build"

  # Verify installation
  echo "Verifying reprostim-capture installation..."
  reprostim-videocapture -V

  # Cleanup reprostim-capture packages
  #
  # Keep runtime packages marked as manual to avoid their removal
  if [[ -n "$REPROSTIM_CAPTURE_PACKAGES_RUNTIME" ]]; then
    echo "Marking reprostim-capture runtime packages as manual to avoid their removal: ${REPROSTIM_CAPTURE_PACKAGES_RUNTIME}"
    apt-mark manual $REPROSTIM_CAPTURE_PACKAGES_RUNTIME
    apt-mark hold $REPROSTIM_CAPTURE_PACKAGES_RUNTIME
  fi

  # Remove dev packages
  echo "Removing reprostim-capture development packages: ${REPROSTIM_CAPTURE_PACKAGES_DEV}"
  apt-get remove --purge -y ${REPROSTIM_CAPTURE_PACKAGES_DEV}
  apt-get autoremove -y
fi

# Remove psychopy-installer
echo "Removing psychopy-installer..."
rm -rf /opt/psychopy-installer

# Remove unnecessary dirs/files from the copied worktree
echo "Cleaning up copied reprostim worktree..."
rm -rf "${REPROSTIM_HOME}/.ai"
rm -rf "${REPROSTIM_HOME}/.git"
rm -rf "${REPROSTIM_HOME}/.github"
rm -rf "${REPROSTIM_HOME}/.idea"
rm -rf "${REPROSTIM_HOME}/.pytest_cache"
rm -rf "${REPROSTIM_HOME}/Events"
rm -rf "${REPROSTIM_HOME}/Parsing"
rm -rf "${REPROSTIM_HOME}/QRCoding"
rm -rf "${REPROSTIM_HOME}/dist"
rm -rf "${REPROSTIM_HOME}/docs"
rm -rf "${REPROSTIM_HOME}/examples/exp-alpha"
rm -rf "${REPROSTIM_HOME}/temp"
rm -rf "${REPROSTIM_HOME}/venv"
rm -rf "${REPROSTIM_HOME}/.gitignore"

# Configure permissions
echo "Configuring permissions to allow non-root users to run PsychoPy and ReproStim..."
if [[ -d /opt ]]; then
  chmod a+rX -R /opt || true
fi
if [[ -d /root/.psychopy3 ]]; then
  chmod a+rX -R /root/.psychopy3 || true
fi

echo "Container setup completed: Python v${PYTHON_VERSION} + PsychoPy v${PSYCHOPY_VERSION} + ReproStim v${REPROSTIM_VERSION}"
