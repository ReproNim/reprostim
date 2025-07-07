#!/bin/bash

thisdir=$(dirname "$0")
tmp_dir="${TMPDIR:-/tmp}"
MODE=${1:-default}

echo "Test CI/CD ReproStim timesync-stimuli.."

echo "tmp_dir=${tmp_dir}"

if [[ "$MODE" == "xvfb" ]]; then
  echo "Running in CI/CD mode on virtual screen"
  # store the tmp_dir in GITHUB_ENV for later use
  echo "tmp_dir=$tmp_dir" >> "$GITHUB_ENV"
else
  echo "Running in default mode on current DISPLAY=$DISPLAY"
fi


export FRAME_WIDTH=1920
export FRAME_HEIGHT=1080
export FRAME_RATE=60
export FRAME_BPP=24
export DISPLAY_PATH="$tmp_dir/reprostim_last_display.txt"
export XVFB_OPTS="-screen 0 ${FRAME_WIDTH}x${FRAME_HEIGHT}x${FRAME_BPP} -ac +extension GLX +render -noreset"
export DISPLAY_START=25
export REPROSTIM_CMD="./run_reprostim_container.sh timesync-stimuli -m event --mute -d \$(cat $tmp_dir/reprostim_last_display.txt)"

cd ${thisdir}

echo "Run Xvfb in background with REPROSTIM_CMD"
xvfb-run -a -n $DISPLAY_START -s "$XVFB_OPTS" bash -c "echo \$DISPLAY > ${DISPLAY_PATH}; $REPROSTIM_CMD"&
XVFB_RUN_PID=$!

echo "Started xvfb-run with PID $XVFB_RUN_PID"
echo "Wait for Xvfb to start"
sleep 4

export DISPLAY=$(cat ${DISPLAY_PATH})
echo "Xvfb started on display: $DISPLAY"
echo "Send test pulse events"
./test_reprostim_events.sh 2 5 5 1.5 20 "${DISPLAY}" &

echo "Record video for 45 seconds"
ffmpeg -video_size "${FRAME_WIDTH}x${FRAME_HEIGHT}" -framerate "${FRAME_RATE}" -f x11grab -i "$DISPLAY" -t 45 -c:v libx264 -pix_fmt yuv420p "$tmp_dir/reprostim_screenshot_$(date +%Y-%m-%d_%H-%M-%S).mp4"
sleep 45
ls -l $tmp_dir/reprostim_*

echo "Kill Xvfb at the end if any"
sleep 1
kill $XVFB_RUN_PID 2>/dev/null || true
wait $XVFB_RUN_PID 2>/dev/null || true