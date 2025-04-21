# Project Structure

## `docs`

Contains all documentation for the `reprostim` project and RTD configuration.

## `src/reprostim`

Contains all code for `reprostim` library. Represented as a set of Python
APIs, tools and utilities under the umbrella of the `reprostim` library,
where each tool is a separate subcommand of the `reprostim` CLI.

## `src/reprostim-capture`

Contains all code needed for setting up `reprostim-videocapture`. This
includes C++ code for interfacing with the video capture device, and
scheme for setting up a video-capture `server`, along with helper
utilities.

This subproject is set of native C/C++ tools and utilities to capture
video/audio signals with Magewell USB Capture devices and save it to a file.
More detailed information about dependencies and installation provided in
[reprostim-capture README.md](./src/reprostim-capture/README.md).

## `tests`

Directory with reprostim pytests and test data.

## `tools`

Placeholder for utility scripts which are used outside the Python package,
potentially for configuration or monitoring of the deployment. Some scripts
could potentially be later recoded and included in the Python package.
