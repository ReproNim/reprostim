# Event relay device

The event relay device is a single-board microcontroller, operated via micropython, which interfaces between input peripherals and an event recording system.


## Input Peripherals

Handheld input pads which are usable inside an MR scanner are connected to the device via a multi-channel cable, the color-coding of which is available in `connector_cable.csv`.

## Installation

### Micropython
A device-type-specific micropython distribution file (e.g. `.uf2` or `.dfu`) will need to be downloaded and flashed onto the microcontroller. 
