#!/bin/bash
# chmod +x ns_05.sh

# Define external variables
NOSIGNAL_ARGS="--number-of-checks 5 --truncated check5"
#NOSIGNAL_ARGS="--number-of-checks 5 --truncated fixup"


# log all to file
LOG_TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="ns_$LOG_TIMESTAMP.log"
# Redirect stdout and stderr to the log file
exec > >(tee -a "$LOG_FILE") 2>&1


DIRECTORY="/data/repronim/reprostim-reproiner/Videos/2024/05"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP] Processing nosignal batch:"
echo "  - DIRECTORY     : $DIRECTORY"
echo "  - NOSIGNAL_ARGS : $NOSIGNAL_ARGS"
echo " "

FILES=("$DIRECTORY"/*.mkv)
TOTAL_FILES=${#FILES[@]}


COUNTER=1
NOSIGNAL_COUNTER=0
NOSIGNAL_FILES=()
for FILE in "${FILES[@]}"
do
  echo " "
  echo "----------------------------------------------"
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$TIMESTAMP] Processing ($COUNTER of $TOTAL_FILES) $FILE ..."
  ./reprostim/nosignal $NOSIGNAL_ARGS "$FILE"
  EXIT_CODE=$?
  echo "EXIT_CODE=$EXIT_CODE"
  if [ $EXIT_CODE -eq 1 ]; then
    echo "[$TIMESTAMP] NOSIGNAL_FILE: $FILE"
    ((NOSIGNAL_COUNTER++))
    NOSIGNAL_FILES+=("$FILE")
  fi
  ((COUNTER++))
done

echo " "
echo "----------------------------------------------"
echo "DIRECTORY      : $DIRECTORY"
echo "NOSIGNAL_ARGS  : $NOSIGNAL_ARGS"
echo " "
echo "TOTAL_FILES    : $TOTAL_FILES"
echo "NOSIGNAL_COUNT : $NOSIGNAL_COUNTER"
for NOSIGNAL_FILE in "${NOSIGNAL_FILES[@]}"
do
  echo "$NOSIGNAL_FILE"
done
echo " "


