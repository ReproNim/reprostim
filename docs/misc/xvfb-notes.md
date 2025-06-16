# Virtual Screen Notes

## Installation & Usage

```shell
sudo apt update
sudo apt install xvfb

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
which xvfb-run

# setup params
export XVFB_OPTS="-screen 0 1920x1080x24 -ac +extension GLX +render -noreset"
export DISPLAY_START=20
export REPROSTIM_CMD="hatch run reprostim timesync-stimuli --mute -d $(cat /tmp/reprostim_last_display.txt)"

# run Xvfb in background with REPROSTIM_CMD
xvfb-run -a -n $DISPLAY_START -s "$XVFB_OPTS" \
  bash -c 'echo $DISPLAY > /tmp/reprostim_last_display.txt; $REPROSTIM_CMD'&


XVFB_RUN_PID=$!
echo "Started xvfb-run with PID $XVFB_RUN_PID"
  
# wait for Xvfb to start
sleep 2

export DISPLAY=$(cat /tmp/reprostim_last_display.txt)
echo "Xvfb started on display: $DISPLAY"

# wait some time to start command
sleep 5

# make screenshot
import -display $DISPLAY -window root "/tmp/reprostim_screenshot${DISPLAY}_$(date +%Y-%m-%d_%H:%M:%S).png"

# kill Xvfb at the end
sleep 1
kill $XVFB_RUN_PID
wait $XVFB_RUN_PID 2>/dev/null
```





