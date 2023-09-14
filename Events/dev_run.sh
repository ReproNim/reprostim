#!/usr/bin/env bash

set -eu -o pipefail

DEBUG=False #capitalized for python interpretation
LOG_FILE= #setting it to empty so that check doesn't fail on account of set -eu
MAIN_BOARD=false
RT_BOARD=false



PREDEFINED_EVENTS=false

DEVICE_MODELS=$(cd devices > /dev/null; ls -d */ | xargs | sed 's/\///g')

USAGE="Usage:\n\
        $(basename "$0") <device_model>\n\
        -h: displays this help message.\n\
        Positional Arguments:\n\
                <device_model>: which device model code to use.\n\
                        Acceptable values are: $DEVICE_MODELS"

# Read options:
while getopts "hdpl:" flag
do
        case "$flag" in
                d)
                        DEBUG=True
                        ;;
                p)
                        PREDEFINED_EVENTS=true
                        ;;
                l)
                        LOG_FILE=${OPTARG}
                        ;;
                h)
                        echo -e "$USAGE"
                        exit 0
                        ;;
                \?)
                        echo "Invalid option: -$OPTARG" >&2
                        exit 1
                        ;;
                :)
                        echo "Option -$OPTARG requires an argument." >&2
                        exit 1
                        ;;
        esac
done

# Shift pointer to read mandatory device model specification.
shift $((OPTIND - 1))
DEVICE_MODEL=${1:-}

if [ -z "$DEVICE_MODEL" ]
then
        echo "$(basename "$0"): no device model specified."
        echo -e "$USAGE"
        exit 1
else
        echo "$DEVICE_MODEL"
fi

if [ -z "$LOG_FILE" ]
then
        echo "$(basename "$0"): no log file specified, using default:"
        LOG_FILE="/tmp/conveyor_log-$(whoami)-$(date)"
        echo "${LOG_FILE}"
fi

pinstates_file="devices/${DEVICE_MODEL}/device_files/pinstates.py"
delay_test_file="devices/${DEVICE_MODEL}/device_files/main.py"


# Required to import from parent Python module:
export PYTHONPATH=$PWD/..


# Figure out which board is the main board and which is used for debugging
mpremote a0 cp "devices/${DEVICE_MODEL}/device_files/roundtripper.py" :roundtripper.py
A0_RTCHECK=$(python -c "from Events import launch; launch.check_roundtripper('/dev/ttyACM0')")

# Copy files to board(s) and assign device nodes to variables for later passing to the Python code.
if [ "$A0_RTCHECK" == "True" ]; then
        mpremote a1 fs cp "${pinstates_file}" :pinstates.py && \
                MAIN_BOARD="/dev/ttyACM1" || \
                echo "A roundtripping (secondary) device was detected, but no additional device can be found to use for pin state detection."
        mpremote a0 fs cp "${delay_test_file}" :main.py
        RT_BOARD="/dev/ttyACM0"
else
        mpremote a0 fs cp "${pinstates_file}" :pinstates.py
        MAIN_BOARD="/dev/ttyACM0"
        mpremote a1 fs cp "${delay_test_file}" :main.py && \
                RT_BOARD="/dev/ttyACM1" || \
                echo "You have connected only one device, meaning that the files for live roundtrip delay testing were not installed, and will not be usable."
fi


# Report detection results, and set debugging (i.e. roundtripping) to false if a roundtripping board cannot be located.
echo "Your main (pin state query) board is located at $MAIN_BOARD"
if [ "$RT_BOARD" = false ]; then
        DEBUG=False
        # We capitalize it here for usage in Python.
        RT_BOARD=False
else
        echo "Your debugging (roundtrip) board is located at $RT_BOARD"
fi
# In this section, we could also report the unique device ID (might have potential debugging relevance 🤔).
# This is queried via:
# mpremote exec 'import machine; import ubinascii as ub; a = ub.hexlify(machine.unique_id()).decode("utf-8"); print(a)'


# Execute Python signal conveyor code.
if [ "$PREDEFINED_EVENTS" = true ] # only run predefined events if there are two boards connected
then
        python -c "from Events import conveyor; conveyor.main($DEBUG)" &
        pid=$!
        cleanup () {
                echo killing $pid
                kill -9 $pid
        }
        trap cleanup EXIT
        python -c "from Events import predefined_events; predefined_events.send_events()" &> /dev/null
else
        python -c "from Events import conveyor; conveyor.convey(devicenode=\"${MAIN_BOARD}\", rt_devicenode=\"${RT_BOARD}\", check_delay=${DEBUG}, log_file=\"${LOG_FILE}\")"
fi
popd
