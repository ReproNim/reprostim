# ReproStim

    ReproStim is a video capture and recording suite for neuroimaging and
    psychology experiments.  Its goal is to provide experimenters with a
    complete record of audio and visual stimulation for every data collection
    session by making it possible to easily collect high fidelity copies of the
    actual stimuli shown to each subject in the form of video files that can be
    stored alongside  behavioral or neuroimaging data in public repositories. 

    ReproStim provides for enhanced experimental reproducibility and a safeguard
    against data loss in cases of data-collection irregularites.  Because
    ReproStim provides an exact record of the actual stimuli delivered during
    any given experimental session, it makes it possible to precisely reproduce
    experimental sessions, even if the original trial sets were randomized and
    precise trial details not recorded. In cases of experimental irregularities,
    such as aborted fMRI runs, unexpected glitches in trial timing, or
    programming errors that cause records of trial conditions to be lost,
    valuable data (which can be especially costly in cases of fMRI of ECog, for
    example) can be recoded and recovered using the audio-visual record provided
    by ReproStim.   

    ReproStim requires minimal effort on behalf of investigators.  Once it is
    setup as the default mode within a behavioral lab or neuroimaging center,
    investigators can reap the benefits of ReproStim without any additional
    effort on the part of invidiual experimenters.  When successfully set up,
    ReproStim runs in the background, silently collecting, cataloging, and
    storing all audio and visual stimulation delivered to experimental subjects. 

# Development

## Dependencies

On Debian

    apt-get install ffmpeg libudev-dev libasound-dev libv4l-dev

## Build

   cd Capture/C++
   make

## Subdirectories Structure

### Capture

    Contains all code needed for setting up video capture. This includes C++
    code for interfacing with the video capture device, and scheme for setting
    up a video-capture "server", along with helper utilities.

### QRCoding

    Contains utilities for embedding QR codes in experimental stimulus-delivery
    programs, such as PsychoPy, or PsychToolbox scripts.

### Parsing

    Contains code needed for segmenting videos to include just the parts of the
    videos that are demarcated by embedded QR codes marking the beginning and
    end of experimental runs. There are also helper tools for identifying
    experimental runs and matching them to the parent experimental paradigm and
    neuroimaging data acquisitions. 
