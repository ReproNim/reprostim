# ReproStim Tools

## Overview

### A. Install Singularity

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

### B. Install ReproNim Containers

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

### C. Run ReproNim TimeSync Script

Make sure the current directory is one under singularity container 
path created in the previous step B:

```shell
cd ./containers/images/repronim
```

Run the script:

```shell
singularity exec ./repronim-psychopy--2024.1.4.sing ${REPROSTIM_PATH}/tools/reprostim-timesync-stimuli output.log 1
``` 
Where `REPROSTIM_PATH` is the local clone of https://github.com/ReproNim/reprostim repository.

Last script parameter is the display ID, which is `1` in this case.  

### D. Update Singularity Container Locally (Optionally)

Optionally, you can update the container locally for development 
and debugging purposes (with overlay):

```shell
singularity overlay create --size 1024 repronim-psychopy--2024.1.4.overlay
sudo singularity exec --overlay repronim-psychopy--2024.1.4.overlay repronim-psychopy--2024.1.4.sing bash
```
As sample install some package:

```shell
apt-get update
apt-get install pulseaudio-utils
pactl
exit
```

And now run the script with overlay:

```shell
singularity exec -B /run/user/$(id -u)/pulse --env PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native --overlay ./repronim-psychopy--2024.1.4.overlay ./repronim-psychopy--2024.1.4.sing ${REPROSTIM_PATH}/tools/reprostim-timesync-stimuli output.log 1
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

TODO: Also limit container resource -c