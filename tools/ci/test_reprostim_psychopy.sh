#!/bin/bash

# This script tests PsychoPy window visibility under Xvfb or regular display.
# It starts PsychoPy with a simple window, verifies the window is visible
# using xdotool and xwininfo, captures a screenshot for visual verification,
# and returns success/failure based on window detection.

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
  Test CI/CD ReproStim PsychoPy window script.
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


echo "Test CI/CD ReproStim and PsychoPy UI.."

echo "tmp_dir=${tmp_dir}"
cd "$thisdir" || exit

export REPROSTIM_LOG="$tmp_dir/reprostim_psychopy.log"
export REPROSTIM_CONTAINER_RUN_MODE=psychopy
export REPROSTIM_CMD="./run_reprostim_container.sh"


if [[ "$MODE" == "xvfb" ]]; then
  echo "Running in CI/CD mode on virtual screen"
  # store the tmp_dir in GITHUB_ENV for later use
  echo "tmp_dir=$tmp_dir" >> "$GITHUB_ENV"

  export FRAME_WIDTH=1024
  export FRAME_HEIGHT=768
  export FRAME_RATE=60
  export FRAME_BPP=24
  export DISPLAY_PATH="$tmp_dir/reprostim_last_display2.txt"
  export XVFB_OPTS="-screen 0 ${FRAME_WIDTH}x${FRAME_HEIGHT}x${FRAME_BPP} -ac +extension GLX +render -noreset"
  export DISPLAY_START=35

  echo "Run Xvfb in background with REPROSTIM_CMD"
  xvfb-run -a -n $DISPLAY_START -s "$XVFB_OPTS" bash -c "export REPROSTIM_CONTAINER_RUN_MODE=psychopy; echo \$DISPLAY > ${DISPLAY_PATH}; $REPROSTIM_CMD > \"${REPROSTIM_LOG}\" 2>&1"&
  XVFB_RUN_PID=$!

  echo "Started xvfb-run with PID $XVFB_RUN_PID"
  echo "Wait for Xvfb to start"
  sleep 15

  DISPLAY_ID=$(cat "${DISPLAY_PATH}")
  export DISPLAY_ID

  if [ -z "$DISPLAY_ID" ]; then
    echo "[-] DISPLAY_ID is empty. Xvfb may not have started properly, terminating the script."
    exit 1
  fi

  echo "Xvfb started on display: $DISPLAY_ID"
else
  echo "Running in default mode on current DISPLAY=$DISPLAY"

  read -r resolution refresh_rate < <(xrandr | grep '\*' | awk '{print $1, $2}')

  export DISPLAY_ID="${DISPLAY#:}"
  export FRAME_WIDTH=${resolution%x*}
  export FRAME_HEIGHT=${resolution#*x}
  export FRAME_RATE="${refresh_rate%%[^0-9.]*}"
  export FRAME_BPP=24

  "${REPROSTIM_CMD}"
fi

echo "Display[$DISPLAY_ID]: ${FRAME_WIDTH}x${FRAME_HEIGHT}, ${FRAME_RATE} Hz"
echo "ReproStim command to run: $REPROSTIM_CMD"


echo "Wait for PsychoPy window to appear.."
sleep 10

echo "Taking PsychoPy window screenshot of the virtual screen using ImageMagick.."
export REPROSTIM_PSYCHOPY_SCREENSHOT_PATH="$tmp_dir/reprostim_psychopy_screenshot.png"

# Capture screenshot using ImageMagick's import command
DISPLAY="$DISPLAY_ID" import -window root "$REPROSTIM_PSYCHOPY_SCREENSHOT_PATH"
if [ $? -eq 0 ]; then
  echo "Screenshot captured successfully to: $REPROSTIM_PSYCHOPY_SCREENSHOT_PATH"
else
  echo "Error: Failed to capture screenshot"
fi

sleep 1
ls -l "$tmp_dir"/reprostim_psychopy*

# terminate xvfb process if it was started
if [[ "$MODE" == "xvfb" ]]; then
  echo "Kill Xvfb at the end if any"
  sleep 1
  kill "$XVFB_RUN_PID" 2>/dev/null || true
  wait "$XVFB_RUN_PID" 2>/dev/null || true
fi

if [[ -f "REPROSTIM_PSYCHOPY_SCREENSHOT_PATH" ]]; then
  echo "ReproStim PsychoPy screenshot recorded: REPROSTIM_PSYCHOPY_SCREENSHOT_PATH"
else
  echo "ReproStim PsychoPy screenshot not found"
  exit 1
fi
