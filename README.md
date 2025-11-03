# Introduction

[![Read the Docs](https://app.readthedocs.org/projects/reprostim/badge/?version=latest)](https://reprostim.readthedocs.io/en/latest/)
[![Tests](https://github.com/ReproNim/reprostim/actions/workflows/pytest.yml/badge.svg)](https://github.com/ReproNim/reprostim/actions/workflows/pytest.yml)
[![PyPI Version](https://img.shields.io/pypi/v/reprostim.svg)](https://pypi.org/project/reprostim/)
[![Docker Image Version](https://img.shields.io/docker/v/repronim/reprostim?sort=semver&label=docker)](https://hub.docker.com/r/repronim/reprostim)
[![Conda](https://img.shields.io/conda/vn/conda-forge/reprostim.svg)](https://anaconda.org/conda-forge/reprostim)
[![GitHub release](https://img.shields.io/github/release/ReproNim/reprostim.svg)](https://GitHub.com/ReproNim/reprostim/releases/)
[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](https://raw.githubusercontent.com/ReproNim/reprostim/master/LICENSES/MIT.txt)

ReproStim is a video capture and recording suite for neuroimaging and
psychology experiments.  Its goal is to provide experimenters with a
complete record of audio and visual stimulation for every data collection
session by making it possible to easily collect high fidelity copies of the
actual stimuli shown to each subject in the form of video files that can be
stored alongside  behavioral or neuroimaging data in public repositories.
ReproStim is part of large ReproFlow process represented in the diagram below:

<object type="image/svg+xml" data="./docs/source/_static/images/reproflow.svg" width="100%" height="600px"></object>


![](docs/source/_static/images/reproflow.svg)
**Fig. 1:** [ReproNim ReproFlow Diagram, OHBM 2024 #2277](https://github.com/ReproNim/artwork/blob/master/posters/ReproFlow-OHBM2024-poster.svg)

**Note:** This is interactive [SVG diagram](https://reprostim.readthedocs.io/en/latest/_images/reproflow.svg), so you
can open it in separate window and click on the boxes to see more.

ReproStim provides for enhanced experimental reproducibility and a safeguard
against data loss in cases of data-collection irregularities.  Because
ReproStim provides an exact record of the actual stimuli delivered during
any given experimental session, it makes it possible to precisely reproduce
experimental sessions, even if the original trial sets were randomized and
precise trial details not recorded. In cases of experimental irregularities,
such as aborted fMRI runs, unexpected glitches in trial timing, or
programming errors that cause records of trial conditions to be lost,
valuable data (which can be especially costly in cases of fMRI of ECog, for
example) can be recoded and recovered using the audiovisual record provided
by ReproStim.

ReproStim requires minimal effort on behalf of investigators.  Once it is
setup as the default mode within a behavioral lab or neuroimaging center,
investigators can reap the benefits of ReproStim without any additional
effort on the part of individual experimenters.  When successfully set up,
ReproStim runs in the background, silently collecting, cataloging, and
storing all audio and visual stimulation delivered to experimental subjects.

**Documentation:** full documentation is available at [Read the Docs](https://reprostim.readthedocs.io/en/latest/).

**Appendix:** ReproFlow Projects

- [BIDS](https://github.com/bids-standard) - brain imaging data structure standard.
- [Birch](https://wiki.curdes.com/bin/view/CdiDocs/BirchUsersManual) - birch interface documentation.
- [CON](https://centerforopenneuroscience.org/) - center for open neuroscience homepage.
- [con/noisseur](https://github.com/con/noisseur) - system for automated verification of entered/displayed information (on another computer).
- [containers/repronim](https://github.com/ReproNim/containers/tree/master/images/repronim) - repronim containers binary `distribution` for reproducible neuroimaging.
- [containers/repronim-reprostim](https://github.com/ReproNim/reprostim/tree/master/containers/repronim-reprostim) - reprostim containers metadata and tools to generate/build binaries.
- [DataLad](https://www.datalad.org/) - distributed data management free and open source tool.
- [DBIC](https://www.dartmouth.edu/dbic/) - Dartmouth brain imaging center.
- [DICOM](https://www.dicomstandard.org/) - digital imaging and communications in medicine standard.
- [HeuDiConv](https://heudiconv.readthedocs.io/en/latest/) - heuristic-centric DICOM converter.
- [Magewell USB Capture](https://www.magewell.com/capture/usb-capture) - Magewell USB Capture devices.
- [MWCapture SDK](https://www.magewell.com/sdk) - Magewell USB Capture SDK and APIs.
- [NeuroDebian](https://neuro.debian.net/) - ultimate neuroscience software platform.
- [NTP](https://en.wikipedia.org/wiki/Network_Time_Protocol) - network time protocol wiki.
- [ReproEvents](https://github.com/ReproNim/reprostim/tree/master/Events) - events listener server and micropython-based firweware for Raspberry Pi event relay devices.
- [reproflow-data-sync](https://github.com/ReproNim/reproflow-data-sync) - DataLad dataset with all samples of recorded `ReproEvents`, `ReproStim`, etc. data for purpose of calibration and establishing processing pipelines.
- [ReproIn](https://github.com/ReproNim/reproin) - setup for automatic generation of shareable, version-controlled BIDS datasets from MR scanners.
- [ReproMon](https://github.com/ReproNim/repromon) - service to monitor data acquisition to alert if anything goes wrong in ReproFlow.
- [ReproStim](https://github.com/ReproNim/reprostim) - automated capture of audio-visual stimuli into BIDS datasets.
- [reprostim-capture](https://github.com/ReproNim/reprostim/tree/master/src/reprostim-capture) - set of tools and utilities to capture video/audio signal with Magewell USB Capture devices and save it to a file. It is a part of the ReproStim project.
