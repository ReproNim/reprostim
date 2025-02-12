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

The `screen` is drawn on `display`....TBD
