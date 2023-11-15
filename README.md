# ReproStim Introduction

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

## Hardware needed 

Before using ReproStim you will need a minimum of the the following
components:

1. Magewell USB Capture Plus device (MWC)

2. Stimulus control computer (SC) with A/V out to presentation device

3. External presentation device (EPD)

4. Video capture computer (VC) with USB-C port

5. Supporting cables including A/V splitter cables

### Simple setup schematic

Given a stimulus presentation computer (SP) that controls the content and
flow of the experimental presentation and presents A/V to experimental
subject on external monitor or projector (EPD), the setup without ReproStim
would be something like:

1. Schematic A.

       ------                -------
       | SC | -- A/V Out --> | EPD |
       ------                -------

    With the addition of ReprosStim, the setup will look like this:

2. Schematic B.

       ------                                 -------
       | SC | -- A/V Out --> A/V Splitter --> | EPD |
       ------                     |           -------
                                  V
                               -------              ------
                               | MWC | -- USB-C --> | VC | 
                               -------              ------
                             
### Original set up without ReproStim

Most experimental setups include something like Schematic A, with a stimulus
control computer (SC) that sends A/V information to the experimental
subject. For example, in the Dartmouth Brain Imaging Center (DBIC),
experimenters can use their own laptop or a dedicated computer in the scan
control room for SC. The External Presentation Device for video (EPDv) in
the DBIC MRI suite is a projector that projects through the wall of the
shielded scan room to a rear-projection screen located at the back of the
MRI scanner bore; and the EPDa (audio) comprises MRI-safe headphones worn on
the subject's head. 

The A/V out connections from SC can be any standard as long as you have the
appropriate adapters, dongles, etc. However, if your Video out does not
support embedded audio (e.g. VGA), then you will need a separate audio out
set of splitters and cables. The Magewell device has standard audio ports to
accomodate this eventuality.

Note: Missing from Schematics A and B, is any connection back to SC that
records subject response information. That's because ReproStim is not
interested in how the subject responds. If you like, imagine arrows pointing
from EPD to a "subject" node, and then more arrows pointing from the subject
node to some response input device (RID?) and back to SC for recording...
ReproStim will not interfere.

#### Magewell USB Capture Plus Family device

The current version of ReproStim has only been developed and tested for the
Magewell USB Capture DVI Plus device (MWC) . However, we anticipate that it
will be relatively painless to support at least all devices in the USB
Capture Plus Family. Information about these devices and supporting software
can all be found at www.magewell.com

#### Video Capture computer (VC), AKA ReproStim Server

The video capture computer (VC) does most of the work for ReproStim. The
software running on this computer runs as a service that is always on as
long as the computer is running, which is all the time. Therefore I will
refer to VC also as the ReproStim server. In a nutshell, the server software
monitors the video signal coming from SC into MWC. If there is any video
coming over the connection, it gets recorded for posterity.

Current development of ReproStim, including our working setup at the DBIC,
uses a Linux box running Debian Linux. We anticipate that any Nix/Mac setup
running on a modern desktop will be amply sufficient as a ReproStim Server,
and should be relatively painless to configure. 

The current DBIC computer is a small-profile desktop that resides in the
control of the scan suite, quietly recording all video presented to all
subjects.

## Dependencies

On Debian

    apt-get install ffmpeg libudev-dev libasound-dev libv4l-dev libyaml-cpp-dev

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

# Installation and Configuration

## Setup USB device with "udev" access

VideoCapture utility internally uses Magewell Capture SDK and to make it working
properly should be executed under "root" account or in case of other account - special 
"udev" rules should be applied there. Program will produce following error when 
executed in environment without proper ownership and permissions for informational
purposes:

    ERROR[003]: Access or permissions issue. Please check /etc/udev/rules.d/ configuration and docs.

For more information from Magewell refer to item #14 from FAQ  
https://www.magewell.com/kb/detail/010020005/All :  

    Can the example codes associated with USB Capture (Plus) devices in SDKv3 work without root authority (sudo) on Linux?

    Yes. Click here to download the file "189-usbdev.rules" (http://www.magewell.com/files/sdk/189-usbdev.zip) ,
    move it to the directory "/etc/udev/rules.d", and then restart your computer.

### 1) Identify the USB Device:

This is optional step, only for information purposes:

    lsusb

And locate line with device, e.g.:

    Bus 004 Device 012: ID 2935:0008 Magewell USB Capture DVI+

In this sample, 2935 is the "Vendor ID", and 0008 is the "Product ID".


### 2) Create "udev" rules
Create text file under "/etc/udev/rules.d/189-reprostim.rules" location with
content listed below:

    ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="2935", TAG+="uaccess"

Note: we can see that "ATTR{idVendor}" value 2935 is equal to one we got in 
step 1) from lsusb utility.

Also sample udev rules configuration added to project under 
"Capture/etc/udev/189-reprostim.rules" location.

### 3) Add user to "plugdev" group
Make sure the user running VideoCapture utility is a member of the 
"plugdev" group, e.g.:

    sudo usermod -aG plugdev TODO_user

### 4) Restart computer
Restart computer to make changes effect.

Note: we tested "sudo udevadm control --reload-rules" command without OS 
restart, but somehow it didn't help, and complete restart was necessary
anyway.


## TODO:

- Build (per above) and install in the PATH
- TODO: cron job
- TODO: add user/group
- ...
- [Parsing/repro-vidsort](./Parsing/repro-vidsort) script (has hardcoded paths) sorts from `incoming/` to
  folders per DICOM accession
- 
