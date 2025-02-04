# repronim-reprostim container

## Overview

This container is designed to provide a reproducible environment to
execute the `reprostim` tool/package commands.


## Draft Dev Notes

To generate the container instructions like `Dockerfile` and `Singularity`
use the following command:

```shell
cd containers/repronim-reprostim
./generate_container.sh
```

This will generate container Dockerfile/Singularity files in format like
`***.repronim-reprostim-{VERSION}`, where `VERSION` is the latest `git` tag
version when specified, or `0.0.1` otherwise.

To build singularity container, use the following command:

```shell
cd containers/repronim-reprostim
./build_singularity.sh
```

To test `reprostim` package version run:
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
