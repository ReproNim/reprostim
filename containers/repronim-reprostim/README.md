# Container `repronim-reprostim`

## Overview

This container is designed to provide a reproducible environment to
execute the `reprostim` tool/package commands.

## ReproStim Singularity Container

### Install Singularity

#### On Linux (Ubuntu 24.04) :

```shell
wget -O- http://neuro.debian.net/lists/noble.de-m.libre | sudo tee /etc/apt/sources.list.d/neurodebian.sources.list
sudo apt-key adv --recv-keys --keyserver hkps://keyserver.ubuntu.com 0xA5D32F012649A5A9

sudo apt-get update

sudo apt-get install singularity-container
```

```shell
$ singularity --version
  singularity-ce version 4.1.1
```

Check that X11 system is used by default in Linux (Ubuntu 24.04),
psychopy will not work well with Wayland:

```
echo $XDG_SESSION_TYPE
```

It should return `x11`. If not, switch to X11:

 - At the login screen, click on your username.
 - Before entering your password, look for a gear icon or "Options" button at the bottom right corner of the screen.
 - Click the gear icon, and a menu should appear where you can select either "Ubuntu on Xorg" or "Ubuntu on Wayland."
 - Choose "Ubuntu on Xorg" to switch to X11.
 - Enter your password and log in. You should now be running the X11 session.



### Install Pre-Built Container

#### On Linux (Ubuntu 24.04) :

Ensure DataLad is installed:

```
sudo apt-get install datalad
```

As next step install and download ReproNim containers:

```
datalad install https://datasets.datalad.org/repronim/containers
datalad update
cd ./containers/images/repronim
datalad get .
```

### Build

To `generate` the container instructions like `Dockerfile` and `Singularity`
use the following command:

```shell
cd containers/repronim-reprostim
./generate_container.sh
```

This will generate container Dockerfile/Singularity files in format like
`***.repronim-reprostim-{VERSION}`, where `VERSION` is the latest `git` tag
version when specified, or `0.0.1` otherwise.

To `build` singularity container, use the following command:

```shell
cd containers/repronim-reprostim
./build_singularity.sh
```

To `test` the singularity container and run `reprostim`, use the following command:

```shell
cd containers/repronim-reprostim
./run_reprostim.sh --help
```

### Run

To test `reprostim` package version in singularity container run:
```shell
singularity exec ./containers/repronim-reprostim/repronim-reprostim-0.7.5.sing python3 -m reprostim --version
```

To run `timesync-stimuli` command with audio codes use the following command:

```shell
export REPROSTIM_PATH=$(pwd)

singularity exec \
  --cleanenv --contain \
  -B /run/user/$(id -u)/pulse \
  -B ${REPROSTIM_PATH} \
  --env DISPLAY=$DISPLAY \
  --env PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native \
  ./containers/repronim-reprostim/repronim-reprostim-0.7.5.sing \
  python3 -m reprostim timesync-stimuli -t 10 --mode interval
```

### Debug & Patch Notes

Optionally, you can update the container locally for development
and debugging purposes (with overlay):

```shell
singularity overlay create \
  --size 1024 \
  repronim-reprostim-0.7.5.overlay

sudo singularity exec \
  --overlay repronim-reprostim-0.7.5.overlay \
  --cleanenv --contain -B ${REPROSTIM_PATH} \
  repronim-reprostim-0.7.5.sing \
  bash
```
As sample install some package:

```shell
apt-get update
apt-get install pulseaudio-utils
pactl
exit
```

Optionally also uninstall current reprostim and install it from the local path:
```shell
sudo singularity exec \
  --overlay repronim-reprostim-0.7.5.overlay \
  --cleanenv --contain -B ${REPROSTIM_PATH} \
  repronim-reprostim-0.7.5.sing \
  /opt/psychopy/psychopy_2024.2.5_py3.10/bin/pip uninstall reprostim


sudo singularity exec \
  --overlay repronim-reprostim-0.7.5.overlay \
  --cleanenv --contain -B ${REPROSTIM_PATH} \
  repronim-reprostim-0.7.5.sing \
  /opt/psychopy/psychopy_2024.2.5_py3.10/bin/pip install ${REPROSTIM_PATH}/dist/reprostim-0.7.8.tar.gz[all,disp_mon]
```



```shell

And now run the script with overlay:

```shell
singularity exec \
  --cleanenv --contain \
  -B /run/user/$(id -u)/pulse \
  -B ${REPROSTIM_PATH} \
  --env DISPLAY=$DISPLAY \
  --env PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native \
  --overlay ./repronim-reprostim-0.7.5.overlay \
  ./repronim-reprostim-0.7.5.sing \
  ${REPROSTIM_PATH}/tools/reprostim-timesync-stimuli output.log 1
```

Where `/run/user/321/pulse` is sample external pulseaudio device path bound to the container. Usually
when you run the script w/o binding it will report error like:

```shell
Failed to create secure directory (/run/user/321/pulse): No such file or directory
```

NOTE: Make sure `PULSE_SERVER` is specified in the container environment and
points to the host pulseaudio server. e.g.:

```shell
export PULSE_SERVER=unix:/run/user/321/pulse/native
```

`REPROSTIM_PATH` is the local clone of https://github.com/ReproNim/reprostim repository.

And all notes for local PC altogether:

```shell
cd ~/Projects/Dartmouth/branches/datalad/containers/images/repronim
export REPROSTIM_PATH=~/Projects/Dartmouth/branches/reprostim

singularity overlay create \
  --size 1024 \
  repronim-reprostim-0.7.5.overlay

sudo singularity exec \
  --overlay repronim-reprostim-0.7.5.overlay \
  repronim-reprostim-0.7.5.sing \
  bash

# execute in shell
apt-get update
apt-get install portaudio19-dev pulseaudio pavucontrol pulseaudio-utils
pactl
exit

# make sure all python packages are installed
sudo singularity exec \
  --overlay repronim-reprostim-0.7.5.overlay \
  repronim-reprostim-0.7.5.sing \
  python3 -m pip install pyzbar opencv-python numpy click pydantic sounddevice scipy pydub pyaudio reedsolo psychopy-sounddevice

# and run the script
rm output.log
singularity exec \
  --cleanenv --contain \
  -B /run/user/$(id -u)/pulse \
  -B ${REPROSTIM_PATH} \
  --env DISPLAY=$DISPLAY \
  --env PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native \
  --overlay ./repronim-reprostim-0.7.5.overlay \
  ./repronim-reprostim-0.7.5.sing \
  python3 -m reprostim timesync-stimuli --display 1

```
