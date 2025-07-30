# Virtual Screen Notes

## Installation & Usage

```shell
sudo apt update
sudo apt install xvfb
sudo apt install xdotool

which xvfb-run
```

Run in background mode as FullHD:
```shell
# use FullHD resolution, disables access control, enables GLX and
# render extensions, no reset at last client exit
export XVFB_OPTS="-screen 0 1920x1080x24 -ac +extension GLX +render -noreset"

# run on display :99
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# or use automatic screen selection
Xvfb --auto-servernum --server-num=20 --auto-servernum --server-num=20 -s "$XVFB_OPTS"

```
Run say `xterm` in background:
```shell
xvfb-run xterm &
```

Make PNG screenshot:
```shell
import -display :99 -window root "screenshot_$(date +%Y-%m-%d_%H:%M:%S).png"
```

Kill Xvfb at the end:
```shell
killall Xvfb
```

## Script Example

Now all together in a script:
```bash
# install Xvfb
sudo apt update
sudo apt install xvfb
sudo apt install xdotool
which xvfb-run

cd tools/ci
./test_reprostim_timesync-stimuli.sh xvfb
```

For more details, see the script: [tools/ci/test_reprostim_timesync-stimuli.sh](https://github.com/ReproNim/reprostim/blob/master/tools/ci/test_reprostim_timesync-stimuli.sh).
