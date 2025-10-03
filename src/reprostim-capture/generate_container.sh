#!/bin/bash

set -eu

generate() {
	# more details might come on https://github.com/ReproNim/neurodocker/issues/330
	[ "$1" == singularity ] && add_entry=' "$@"' || add_entry=''
	#neurodocker generate "$1" \
	ndversion=0.9.5
	#ndversion=master
	echo "Using Neurodocker version: $ndversion, add_entry='$add_entry'"
	docker run --rm repronim/neurodocker:$ndversion generate "$1" \
		--base-image=neurodebian:bookworm \
		--ndfreeze date=20240505 \
		--pkg-manager=apt \
		--install vim wget strace time ncdu gnupg curl procps datalad pigz less tree \
				  git-annex \
                  ffmpeg mediainfo \
                  libudev-dev libasound-dev libv4l-dev libyaml-cpp-dev libspdlog-dev catch2 v4l-utils libopencv-dev libcurl4-openssl-dev nlohmann-json3-dev \
                  cmake g++ \
                  python3-pydantic python3-opencv python3-numpy python3-click python3-pytest python3-pytest-cov \
		--user=reproin
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
