#!/bin/bash

# Script to simulate pulse events using xdotool
# Usage: ./test_reprostim_events.sh NUM_SERIES SERIES_INTERVAL NUM_EVT EVT_INTERVAL [SLEEP_DELAY] [DISPLAY]
# Make sure to set DISPLAY if using Xvfb

NUM_SERIES="$1"
SERIES_INTERVAL="$2"
NUM_EVT="$3"
EVT_INTERVAL="$4"
SLEEP_DELAY="${5:-0}"
DISPLAY_PARAM="$6"

# Use passed-in DISPLAY if provided
if [[ -n "$DISPLAY_PARAM" ]]; then
  export DISPLAY="$DISPLAY_PARAM"
fi

echo "DISPLAY is set to: $DISPLAY"

sleep "$SLEEP_DELAY"

# Validate inputs
if [ -z "$NUM_SERIES" ] || [ -z "$SERIES_INTERVAL" ] || [ -z "$NUM_EVT" ] || [ -z "$EVT_INTERVAL" ]; then
  echo "Usage: $0 <number_of_series> <series_interval> <number_of_events> <events_interval> [<sleep_delay>] [<display>]"
  exit 1
fi

start_time=$(date +%s)

for (( series=1; series<=NUM_SERIES; series++ )); do
  echo "Starting series $series"
  for (( event=1; event<=NUM_EVT; event++ )); do
    echo "Sending pulse event $series.$event"
    xdotool key 5
    sleep "$EVT_INTERVAL"
  done

  if [ "$series" -lt "$NUM_SERIES" ]; then
    echo "Waiting $SERIES_INTERVAL seconds before next series..."
    sleep "$SERIES_INTERVAL"
  fi
done

# Escape and quit the application
echo "Finishing up and send ESC q ESC..."
xdotool key Escape
sleep 0.2
xdotool key q
sleep 0.2
xdotool key Escape

end_time=$(date +%s)
dt=$(( end_time - start_time ))

echo "Done. Execution time: $dt seconds"
