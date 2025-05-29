Notes for setting up QA cycle at DBIC
-------------------------------------

base system is ??? running Debian GNU/Linux with NeuroDebian repos on top bookworm.

All activities are running under "reprostim" user.

We configured automated login for reprostim user into GNOME desktop

- uses gdm3
- configured it to autostart session for reprostim user

At the end of /etc/gdm3/daemon.conf added::

    [daemon]
    AutomaticLoginEnable=true
    AutomaticLogin=reprostim

- only Gnome (not Gnome classic of XFCE) somehow manage to not go into "black
  screen only"   mode whenever gdm3 restarts when HDMI is not connected
  yet, as e.g. during reboot.

- but in Gnome we get that damn overview instead of desktop!
  - apt install gnome-shell-extension-dashtodock
  - went to Extensions configuration, in dash to dock Settings -> Appearance disabled "Show overview on startup"

under Xorg where we logged into Gnome and ran Settings

- disabled power management
- disabled auto locking of the screen

Now running the following script works!

    reprostim@reproiner:~/proj/repronim/ses-20250529-auto$ cat ./run-repronim-reprostim
    #!/bin/bash

    cd $(dirname $0)

    DISPLAY=:0 singularity exec \
            -B /run/user/$(id -u)/pulse \
            containers/images/repronim/repronim-reprostim-0.7.13.sing \
            /opt/psychopy/psychopy_2024.2.5_py3.10/bin/reprostim \
            timesync-stimuli --mode event  -t 100000 "$@"

A version of it was adapted into actual "deployment"


After reboot GNOME session did not react to me connecting the cable . I did
have to restart gdm3 while it was connected so it got idea about display
first.  So we still have that issue :-/  But setup should work until the next reboot
