# Display Monitoring Notes

## Overview

As part of [#120](https://github.com/ReproNim/reprostim/issues/120) issue, we
need in some kind of hook/monitor to catch events related to researcher
video output. Ideally it should be cross-platform or at least Linux and
XOS to be supported. Scenario is that researcher brings laptop to MRI
scanner console room, connect it to birch, network and A/V out to VGA
splitter to send video/audio signal to room monitor, video projector,
headphones, etc.

On one side we have physical port like HDMI, DVI, DisplayPort  from
hardware on researcher laptop, and cable that can be connected to VGA
splitter.

On other side we have PsychoPy based script on the same researcher laptop
which can generate video signal and play it on certain `screen` (can be
specified via `--display` option in `timesync-stimuli` reprostim command).

The script plays video using PsychoPy visual API. After some research it
looks like internally can be used different backends like [pyglet](http://www.pyglet.org),
[pygame](http://www.pygame.org) or [glfw](https://www.glfw.org). Default is
`pyglet` one. `pygame` probably doesn't support multiple `screen`s.
`screen` is some kind of logical/abstract thing which is tied to backend like `pyglet` or `glfw`.

In general video stack can be described as stack of layers like below:

* `V1`: Physical video card or device with one of ports like HDMI, DVI, D-Sub,
DisplayPort, USB-C etc.
* `V2`: OS specific virtual `display` model. It handled by OS and bound to
`V1` video device.
* `V3`: PsychoPy visual backend (`pyglet`, `pygame` or `glfw`) which can have
one or multiple virtual `screen`s bound to `display` from `V2`.
* `V4`: Researcher specific script operating with PsychoPy `screen` via visual
API to render data. In our case this is `timesync-stimuli` script orchestrating
stimuli/QR codes data.

Note: each layer has own identification model for related video device and on
some layers it's OS/hardware specific. Sometimes we don't have strict correlation
between layers.

Problem: we have some events on low layer `V1` from hardware, and it should be
monitored and mapped to logical `V4` one. Possible matrix listed below, but
currently only Linux with X11 and OSX 10.6+ are going to be supported:

| Layer | Linux+X11                  | OSX      | Windows    |
|-------|----------------------------|----------|------------|
| `V1`  | pyudev                     | Quartz   | Win32, WMI |
| `V2`  | randr, python-xlib, xrandr | Quartz   | Win32, WMI |
| `V3`  | pyglet                     | pyglet   | pyglet     |
| `V4`  | PsychoPy                   | PsychoPy | PsychoPy   |


## Appendix

### MacOS Installation Notes

Display monitoring functionality moved to separate extra dependency `[disp_mon]`
and included in `[all]` one. But it happened that under some MacOS systems
`[disp_mon]` conflicts with `[psychopy]`/`[audio]` ones on package manager level.
Issue is not resolved ATM in clean way, but if someone still need to run scripts
using psychopy or audio, like `timesync-stimuli`, it can be temporary bypassed
as listed below (in development mode):

```shell
hatch env remove
hatcn env create
hatch run pip install -e .[psychopy]
hatch run pip install -e .[audio]
hatch run reprostim timesync-stimuli -w -z 600 400
```
