#!/usr/bin/env bash

DEBUG=False #capitalized for python interpretation

PREDEFINED_EVENTS=false

DEVICE_MODELS=$(cd devices > /dev/null; ls -d */ | xargs | sed 's/\///g')

USAGE="Usage:\n\
        $(basename "$0") <device_model>\n\
        -h: displays this help message.\n\
        Positional Arguments:\n\
                <device_model>: which device model code to use.\n\
                        Acceptable values are: $DEVICE_MODELS"

# reads options:
while getopts "hdp" flag
do
        case "$flag" in
                d)
                        DEBUG=True
                        ;;
                p)
                        PREDEFINED_EVENTS=true
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

# shifts pointer to read mandatory device model specification
shift $((OPTIND - 1))
DEVICE_MODEL=${1}

if [ -z "$DEVICE_MODEL" ]
then
        echo "$(basename "$0"): no device model specified."
        echo -e "$USAGE"
        exit 1
else
        echo "$DEVICE_MODEL"
fi

pinstates_file="devices/${DEVICE_MODEL}/device_files/pinstates.py"
delay_test_file="devices/${DEVICE_MODEL}/device_files/main.py"
#echo "Running \`mpremote fs cp \"${pinstates_file}\" :pinstates.py && python conveyor.py\`."
mpremote a0 fs cp "${pinstates_file}" :pinstates.py
mpremote a1 fs cp "${delay_test_file}" :main.py || \
        echo "You have connected only one device, meaning that the files for live roundtrip delay testing were not installed, and will not be usable."
pushd ..

if [ "$PREDEFINED_EVENTS" = true ] # only run predefined events if there are two boards connected
then
        python -c "from Events import conveyor; conveyor.main($DEBUG)" &
        pid=$!
        cleanup () {
                echo killing $pid
                kill -9 $pid
        }
        trap cleanup EXIT
        python -c "from Events import predefined_events; predefined_events.send_events()"
else
        python -c "from Events import conveyor; conveyor.main($DEBUG)" 
fi
popd
