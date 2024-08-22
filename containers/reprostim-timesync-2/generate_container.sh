#!/bin/bash

set -eu

generate() {
	[ "$1" == singularity ] && add_entry=' "$@"' || add_entry=''
	#neurodocker generate "$1" \
	ndversion=1.0.1
	#ndversion=master
		#--ndfreeze date=20240801 \
    # Thought to use conda-forge for this, but feedstock is not maintained:
    #  https://github.com/conda-forge/psychopy-feedstock/issues/64
    # --miniconda version=py312_24.5.0-0 conda_install="conda-forge::psychopy conda-forge::qrcode" \
    # Had to go with 3.11 due to https://stackoverflow.com/questions/77364550/attributeerror-module-pkgutil-has-no-attribute-impimporter-did-you-mean
    # Need extra -dev libraries etc to install/build wxpython
    # sudo needed for the psychopy-installer script: https://github.com/wieluk/psychopy_linux_installer/issues/11
	docker run --rm repronim/neurodocker:$ndversion generate "$1" \
		--base-image=neurodebian:bookworm \
		--pkg-manager=apt \
		--install build-essential pkg-config git \
          sudo \
          libgtk-3-dev libwxgtk3.2-dev libwxgtk-media3.2-dev libwxgtk-webview3.2-dev libcanberra-gtk3-module \
          libusb-1.0-0-dev portaudio19-dev libasound2-dev \
          vim wget strace time ncdu gnupg curl procps pigz less tree python3 python3-pip \
        --run "git clone https://github.com/wieluk/psychopy_linux_installer/ /opt/psychopy-installer; cd /opt/psychopy-installer; git checkout 21b1ac36ee648e00cc3b68fd402c1e826270dad6" \
		--run "/opt/psychopy-installer/psychopy_linux_installer.sh --install_dir=/opt/psychopy --psychopy_version=2024.1.4 --bids_version=2023.2.0 --python_version=3.10.14 --wxpython_version=4.2.1 -v -f" \
        --user=reproin \
#        \
#		--run "$run_cmd" \
#		--run "apt-get update && apt-get -y dist-upgrade" \
#		--run "curl -sL https://deb.nodesource.com/setup_20.x | bash - " \
#		--install nodejs \
#		--run "npm install -g bids-validator@1.14.5" \
#		--run "mkdir /afs /inbox" \
#		--copy bin/reproin /usr/local/bin/reproin \
#		--run "chmod a+rx /usr/local/bin/reproin" \
#		--entrypoint "/usr/local/bin/reproin$add_entry"
}

generate docker > Dockerfile
generate singularity > Singularity
