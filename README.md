# TITLE

Describe what it is for

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
