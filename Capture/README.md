# ReproStim Capture

## Overview

Capture project is set of tools and utilities to capture video/audio signal with Magewell
USB Capture devices and save it to a file. It is a part of the ReproStim project.

## Dependencies

On Debian:

    apt-get install -y ffmpeg libudev-dev libasound-dev libv4l-dev libyaml-cpp-dev libspdlog-dev v4l-utils libopencv-dev cmake g++

Project requirements:
   - OS Linux
   - g++ (C++17)
   - CMake 3.10+
   - Packages:
     - Magewell Capture SDK for Linux 3.3.1.1313
     - libv4l2
     - libv4l-dev
     - libudev-dev
     - libasound-dev
     - libyaml-cpp-dev
     - libspdlog-dev
     - libopencv-dev
     - v4l-utils
     - ffmpeg
 


## Build

Capture uses CMake as build system. To build the project, run the following commands:

    cd Capture

    mkdir build
    cd build
    cmake ..
    make


## Project Structure

Capture project consists of the following components:
   - `capturelib` - shared static C++ library with common code across all utilities.
   - `screencapture` - project source code for "reprostim-screencapture" command-line 
utility. The program captures screenshots from Magewell USB Capture device and saves 
it as series of image files (*.png).
   - `videocapture` - project source code for "reprostim-videocapture" command-line
utility. The program captures video/audio streams from Magewell USB Capture device 
and saves it as video file (*.mkv).
    

Both utilities use `capturelib` as a shared library.

## Versioning

Current model consists of two versions: explicit and implicit. Explicit version 
is specified in "version.txt" file and considered as the main one. Implicit version 
is a git describe tag reported in --version output as "Build tag".

All projects (capturelib, screencapture, videocapture) use the same versioning data.
It is stored in "version.txt" file in the root of the project. This is plain text file
with the following content: "{MAJOR}.{MINOR}.{PATCH}.{BUILD}". The file is used to 
set the version. Where {MAJOR}, {MINOR} and {PATCH} values should be set manually. While
{BUILD} value can be automatically updated by the build system in IDE or similar.

We also have CMake script "version-auto-inc.cmake" which can be used to increment 
build number in version file during development process:
    
        cd Capture

        cmake -P version-auto-inc.cmake


E.g. in CLion IDE, you can add "version-auto-inc.cmake" as External Tool under
"Settings -> Tools -> External Tools":

![External Tools in CLion](docs/images/clion_version_auto_inc.png)

Then you can run it from the IDE to increment build number manually or integrate it
with build process (as pre-build hook) to increment build number automatically.