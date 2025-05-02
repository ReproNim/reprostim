`reprostim` is packaged and available from many different sources.

## Dependencies

Make sure you have strict Python version/venv especially for sub-commands working
with PsychoPy like `timesync-stimuli`. Recommended Python version is `3.10` ATM:

`qr-parse` subcommand requires `zbar` to be installed:
 - On Debian
   ```shell
       apt-get install -y libzbar0
   ````
 - On MacOS
   ```shell
       brew install zbar
   ```
   NOTE: Consider this conversation in case of problems to install it @MacOS:
         https://github.com/ReproNim/reprostim/pull/124#issuecomment-2599291577

`timesync-stimuli` sub-command requires in `psychopy` and `portaudio` to
be installed:
 - On Debian
   ```shell
       apt-get install portaudio19-dev
   ```
 - On MacOS
   ```shell
       brew install portaudio
   ```

`reprostim-videocapture` utility works only on Linux and requires in
the following packages (build and runtime):

```shell
    apt-get install -y ffmpeg libudev-dev libasound-dev libv4l-dev libyaml-cpp-dev libspdlog-dev catch2 v4l-utils libopencv-dev libcurl4-openssl-dev nlohmann-json3-dev cmake g++
````
Optionally, `con/duct` tool is used to monitor and log system info for
the video capture with `ffmpeg`:

```shell
    pip install con-duct
    duct --version
```


## Local

Released versions of `reprostim` are available on [PyPI](https://pypi.org/project/reprostim)
and [conda](https://github.com/conda-forge/reprostim-feedstock#installing-reprostim).
If installing through `PyPI`, e.g. :
   ```shell
       pip install reprostim[all]
   ```

On Debian-based systems, we recommend using [NeuroDebian](http://neuro.debian.net) as
a basic environment.

`reprostim-videocapture` utility is not available as a separate package at the moment,
and it should be built from the source manually like described below in
[Developers Install](install.md#developers-install) section.

Then, to install the project binaries under `/usr/local/bin`, once the build done,
run the following command:

```shell
    cd src/reprostim-capture

    cmake --install build
```

And make sure the system in configured as described in
[Hardware Setup](install.md#hardware-setup) section.


## Singularity

If [Singularity](https://www.sylabs.io/singularity/) is available on your system,
you can use it to run pre-built containers available at
[DataLad](https://datasets.datalad.org/repronim/containers/images/repronim/).

Note: at this moment the latest containers are not uploaded to the DataLad.

Container binaries stored in format like `repronim-reprostim-{VERSION}.sing` there, e.g.:
`repronim-reprostim-0.7.9.sing`.

So, download containers first from DataLad:

```
datalad install https://datasets.datalad.org/repronim/containers
datalad update
cd ./containers/images/repronim
datalad get .
```

And use necessary container binary to run `reprostim` commands.

```shell
export REPROSTIM_PATH={Specify path to the reprostim repo}

singularity exec \
  --cleanenv --contain \
  -B /run/user/$(id -u)/pulse \
  -B ${REPROSTIM_PATH} \
  --env DISPLAY=$DISPLAY \
  --env PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native \
  ./containers/images/repronim/repronim-reprostim-0.7.9.sing \
  python3 -m reprostim timesync-stimuli -t 10 --mode interval
```

More details can be found in
[Container `repronim-reprostim`](../notes/containers.rst) section.

## Reproiner

We have installed and configured `reprostim-videocapture` utility
on `reproiner` Debian box manually as it's not available as a package yet.

Utility configuration and captured video files are stored under
`/data/reprostim/` location. The `config.yaml` file was copied from
default GitHub version and manually modified to match the system,
connected devices and `reproiner` environment. This directory should be
used as working directory for `reprostim-videocapture` utility.

```shell
  ssh reprostim@reproiner

  cd /data/reprostim
```

Video files are stored under `/data/reprostim/Videos/` location.


We use `screen` utility to run sessions in the background, under `reprostim`
user and share it between other users. The command below will list all
available sessions:

```shell
    screen -ls
```

And connect to the target session with `reprostim-videocapture` utility with:

```shell
    screen -r <SESSION_ID>
```

To create the latest build - checkout `reprostim` project, build and install
it as described in [Developers Install](install.md#developers-install) and
[Local](install.md#local) sections.

```shell
    git clone https://github.com/ReproNim/reprostim.git

    cd src/reprostim-capture

    mkdir build
    cd build
    cmake ..
    make

    cd ..
    cmake --install build
```
As result, it will install `reprostim` package under `/usr/local/bin` location.

Usually in `screen` we have multiple sessions running under `/data/reprostim/`
location like listed below:
- **(A)** `reprostim proc` to run `reprostim-videocapture` utility:
```shell
  reprostim-videocapture -d /data/reprostim -f /data/reprostim/logs/$(date --iso=minutes).log
```
Note: when manually restarting `reprostim-videocapture` utility, make sure that
old `ffmpeg` and `reprostim-videocapture` processes are killed first, e.g.:
```shell
  ps aux | grep videocapture
  ps aux | grep ffmpeg
```
- **(B)** `reprostim logs` to view logs in realtime, e.g.:
```shell
  tail -f /data/reprostim/logs/2024-06-21T08:38-04:00.log
```
- **(C)** `repromon podman` to run `repromon` service.
```shell
  cd /home/reprostim/repromon

  ( set -a &&  source ./.env.dev && podman-compose  -f docker-compose.dev.yml up -d  ; )

  podman ps -a
  podman logs repromon_db_1
  podman logs repromon_web_1
```
- **(D)** `bash` to monitor system and run miscellaneous tasks.

Recently were added cron job to run `reprostim-videocapture` utility
automatically under `/data/reprostim/code/reprostim-videocapture-cron`
location.

Videos captured by `reprostim-videocapture` utility @`reproiner` under
`/data/reprostim/Videos` location are populated and distributed to other
servers (like `rolando` or `typhon`) with `git-annex` assistant help.
E.g. @`typhon` git-annex repository is stored under
`/data/repronim/reprostim-reproiner` location.


## Developers Install

`reprostim-videocapture` utility can be built from source with CMake:

```shell
    cd src/reprostim-capture

    mkdir build
    cd build
    cmake ..
    make
```

If you want to build `reprostim` from source locally for development
purposes, you can do this by cloning the
[repository](https://github.com/ReproNim/reprostim) .
To build the project, use `hatch` and `venv` with preferable Python
`3.10` version:

```shell
    # first setup python and hatch
    python3.10 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install hatch

    # build reprostim package
    hatch build reprostim

    # optionally re-create env
    hatch env remove
    hatch env create

    # install all extra dependencies
    hatch run pip install -e .[all]

    # run some reprostim commands, e.g.:
    hatch run reprostim --help
    hatch run reprostim --version
    hatch run reprostim echo 'Hello ReproStim CLI!'
```

## Hardware Setup

### Setup USB device with "udev" access

The `reprostim-videocapture` utility internally uses Magewell Capture SDK and to
make it working properly should be executed under "root" account or in case of
other account - special "udev" rules should be applied there. Program will
produce following error when executed in environment without proper ownership
and permissions for informational purposes:

    ERROR[003]: Access or permissions issue. Please check /etc/udev/rules.d/ configuration and docs.

For more information refer to item #14 from Magewell FAQ on https://www.magewell.com/kb/detail/010020005/All :

    14. Can the example codes associated with USB Capture (Plus) devices in SDKv3 work
        without root authority (sudo) on Linux?

    Yes. Click here to download the file "189-usbdev.rules" (http://www.magewell.com/files/sdk/189-usbdev.zip) ,
    move it to the directory "/etc/udev/rules.d", and then restart your computer.

NOTE: Also make sure that no other processes like ffmpeg, vlc, etc. are using this video device, as
it can accidentally produce the same error message ERROR[003].

#### 1) Identify the USB Device:

This is optional step, only for information purposes:

```shell
    lsusb
```

And locate line with device, e.g.:

    Bus 004 Device 012: ID 2935:0008 Magewell USB Capture DVI+

In this sample, 2935 is the "Vendor ID", and 0008 is the "Product ID".

Optionally Magewell device name and serial number can be quickly checked with this command:

```shell
    lsusb -d 2935: -v | grep -E 'iSerial|iProduct'
```

#### 2) Create "udev" rules
Create text file under "/etc/udev/rules.d/189-reprostim.rules" location with
appropriate content depending on system type.

For an active/desktop user logged in via session manager it should be like:

    ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="2935", TAG+="uaccess"

For a daemon configuration we should provide explicit permissions like:

    SUBSYSTEM=="usb", ATTR{idVendor}=="2935", MODE="0660", OWNER="reprostim", GROUP="plugdev"

Note: we can see that "ATTR{idVendor}" value 2935 is equal to one we got in
step 1) from lsusb utility.

Also sample udev rules configuration added to project under
"src/reprostim-capture/etc/udev/189-reprostim.rules" location.

Note: make sure the file has owner "root", group "root" and 644 permissions:

```shell
    ls -l /etc/udev/rules.d/189*
````
```
    -rw-r--r-- 1 root root 72 ... /etc/udev/rules.d/189-reprostim.rules
```

#### 3) Add user to "plugdev" group
Make sure the user running `reprostim-videocapture` utility is a member of the
"plugdev" group, e.g.:

```shell
    sudo usermod -aG plugdev TODO_user
```

#### 4) Restart computer
Restart computer to make changes effect.

Note: we tested "sudo udevadm control --reload-rules" command without OS
restart, but somehow it didn't help, and complete restart was necessary
anyway.
