#!/bin/bash

set -eu


PYTHON_VERSION=3.10

PSYCHOPY_VERSION=2024.2.5
PSYCHOPY_INSTALL_DIR=/opt/psychopy
PSYCHOPY_HOME=${PSYCHOPY_INSTALL_DIR}/psychopy_${PSYCHOPY_VERSION}_py${PYTHON_VERSION}

REPROSTIM_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.1")
# Decided to go without version to make diff easier to analyze etc
REPROSTIM_SUFFIX=repronim-reprostim # -${REPROSTIM_VERSION}


generate() {
	[ "$1" == singularity ] && add_entry=' "$@"' || add_entry=''
	ndversion=1.0.1
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
        --run "git clone https://github.com/wieluk/psychopy_linux_installer/ /opt/psychopy-installer; cd /opt/psychopy-installer; git checkout tags/v1.4.3" \
		    --run "/opt/psychopy-installer/psychopy_linux_installer --install-dir=${PSYCHOPY_INSTALL_DIR} --psychopy-version=${PSYCHOPY_VERSION} --additional-packages=psychopy_bids==2024.2.2 --python-version=${PYTHON_VERSION} --wxpython-version=4.2.2 -v -f" \
        --run "${PSYCHOPY_HOME}/bin/pip install reprostim[all,disp_mon]==${REPROSTIM_VERSION}" \
        --run "bash -c 'ln -s ${PSYCHOPY_HOME}/bin/psychopy /usr/local/bin/'" \
        --run "bash -c 'b=\$(ls ${PSYCHOPY_HOME}/bin/python3); echo -e \"#!/bin/sh\n\$b \\\"\\\$@\\\"\" >| /usr/local/bin/python3; chmod a+x /usr/local/bin/python3'" \
        --entrypoint python3
#       --user=reproin \
}

echo "Generating containers for Python v${PYTHON_VERSION} + PsychoPy v${PSYCHOPY_VERSION} + ReproStim v${REPROSTIM_VERSION}.."
#
echo "Dockerfile.${REPROSTIM_SUFFIX} ..."
generate docker > Dockerfile.${REPROSTIM_SUFFIX}

echo "Singularity.${REPROSTIM_SUFFIX} ..."
generate singularity > Singularity.${REPROSTIM_SUFFIX}
