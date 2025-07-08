#!/bin/bash

####################################################
# help begin
show_help() {
  cat << EOF
Usage: $0 [MODE]

Arguments:
  MODE           Mode to run the script in. Use 'xvfb' to run it on virtual
                 screen or omit this argument to run on the current DISPLAY.

Options:
  -h, --help     Show this help message and exit

Description:
  Test CI/CD ReproStim timesync-stimuli script.
EOF
}

# Check for help argument
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  show_help
  exit 0
fi
# help end
####################################################

thisdir=$(dirname "$0")
tmp_dir="${TMPDIR:-/tmp}"
MODE=${1:-default}
LOG_LEVEL=DEBUG


echo "Test CI/CD ReproStim timesync-stimuli.."

echo "tmp_dir=${tmp_dir}"
cd ${thisdir}

# Specify test events scenario configuration
SERIES_COUNT=2
SERIES_INTERVAL_SEC=5
EVENTS_IN_SERIES_COUNT=5
EVENTS_INTERVAL_SEC=1.5
EVENTS_STARTUP_DELAY_SEC=20
VIDEO_DURATION_SEC=45


if [[ "$MODE" == "xvfb" ]]; then
  echo "Running in CI/CD mode on virtual screen"
  # store the tmp_dir in GITHUB_ENV for later use
  echo "tmp_dir=$tmp_dir" >> "$GITHUB_ENV"

  export FRAME_WIDTH=1920
  export FRAME_HEIGHT=1080
  export FRAME_RATE=60
  export FRAME_BPP=24
  export DISPLAY_PATH="$tmp_dir/reprostim_last_display.txt"
  export XVFB_OPTS="-screen 0 ${FRAME_WIDTH}x${FRAME_HEIGHT}x${FRAME_BPP} -ac +extension GLX +render -noreset"
  export DISPLAY_START=25
  export REPROSTIM_CMD="./run_reprostim_container.sh timesync-stimuli -m event --mute -d \$(cat $tmp_dir/reprostim_last_display.txt)"

  echo "Run Xvfb in background with REPROSTIM_CMD"
  xvfb-run -a -n $DISPLAY_START -s "$XVFB_OPTS" bash -c "echo \$DISPLAY > ${DISPLAY_PATH}; $REPROSTIM_CMD"&
  XVFB_RUN_PID=$!

  echo "Started xvfb-run with PID $XVFB_RUN_PID"
  echo "Wait for Xvfb to start"
  sleep 4

  export DISPLAY_ID=$(cat ${DISPLAY_PATH})
  echo "Xvfb started on display: $DISPLAY_ID"
else
  echo "Running in default mode on current DISPLAY=$DISPLAY"

  read resolution refresh_rate < <(xrandr | grep '*' | awk '{print $1, $2}')

  export DISPLAY_ID="${DISPLAY#:}"
  export FRAME_WIDTH=${resolution%x*}
  export FRAME_HEIGHT=${resolution#*x}
  export FRAME_RATE="${refresh_rate%%[^0-9.]*}"
  export FRAME_BPP=24
  export REPROSTIM_CMD="./run_reprostim_container.sh timesync-stimuli -m event --mute -d \${DISPLAY_ID}"

fi

echo "Display[$DISPLAY_ID]: ${FRAME_WIDTH}x${FRAME_HEIGHT}, ${FRAME_RATE} Hz"
echo "ReproStim command to run: $REPROSTIM_CMD"

echo "Send test pulse events"
./test_reprostim_events.sh "$SERIES_COUNT" "$SERIES_INTERVAL_SEC" "$EVENTS_IN_SERIES_COUNT" "$EVENTS_INTERVAL_SEC" "$EVENTS_STARTUP_DELAY_SEC" "${DISPLAY_ID}" &

echo "Record video for $VIDEO_DURATION_SEC seconds"
START_TS="$(date '+%Y.%m.%d-%H.%M.%S').000"
END_TS="$(date -d "+$VIDEO_DURATION_SEC seconds" '+%Y.%m.%d-%H.%M.%S').000"
export REPROSTIM_SCREENSHOT_PATH="$tmp_dir/reprostim_screenshot_${START_TS}--${END_TS}.mkv"
echo "ffmpeg -video_size \"${FRAME_WIDTH}x${FRAME_HEIGHT}\" -framerate \"${FRAME_RATE}\" -f x11grab -i \"$DISPLAY_ID\" -t \"$VIDEO_DURATION_SEC\" -c:v libx264 -pix_fmt yuv420p \"$REPROSTIM_SCREENSHOT_PATH\""
ffmpeg -video_size "${FRAME_WIDTH}x${FRAME_HEIGHT}" -framerate "${FRAME_RATE}" -f x11grab -i "$DISPLAY_ID" -t 45 -c:v libx264 -pix_fmt yuv420p "$REPROSTIM_SCREENSHOT_PATH"
sleep $VIDEO_DURATION_SEC
sleep 3
ls -l $tmp_dir/reprostim_*

# terminate xvfb process if it was started
if [[ "$MODE" == "xvfb" ]]; then
  echo "Kill Xvfb at the end if any"
  sleep 1
  kill $XVFB_RUN_PID 2>/dev/null || true
  wait $XVFB_RUN_PID 2>/dev/null || true
fi

if [[ -f "$REPROSTIM_SCREENSHOT_PATH" ]]; then
  echo "ReproStim screenshot video recorded: $REPROSTIM_SCREENSHOT_PATH"
  echo "Parse QR code from the video..."
  QRINFO_VIDEO_PATH="$tmp_dir/${START_TS}--${END_TS}.mkv"
  QRINFO_JSONL_PATH="$REPROSTIM_SCREENSHOT_PATH.qrinfo.jsonl"
  QRINFO_LOG_PATH="$REPROSTIM_SCREENSHOT_PATH.qrinfo.log"
  echo "Create temp QR video file: $QRINFO_VIDEO_PATH"
  cp "$REPROSTIM_SCREENSHOT_PATH" "$QRINFO_VIDEO_PATH"
  ./run_reprostim_container.sh --log-level $LOG_LEVEL qr-parse "$QRINFO_VIDEO_PATH" >"$QRINFO_JSONL_PATH" 2>"$QRINFO_LOG_PATH"
  echo "Remove temp QR video file: $QRINFO_VIDEO_PATH"
  rm -f "$QRINFO_VIDEO_PATH"
else
  echo "ReproStim screenshot video not found"
fi

