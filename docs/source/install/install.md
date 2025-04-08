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


## Local

Released versions of `reprostim` are available on [PyPI](https://pypi.org/project/reprostim)
and [conda](https://github.com/conda-forge/reprostim-feedstock#installing-reprostim).
If installing through `PyPI`, e.g. :
   ```shell
       pip install reprostim[all]
   ```

On Debian-based systems, we recommend using [NeuroDebian](http://neuro.debian.net) as
a basic environment.

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
