#!/usr/bin/env bash

DEBUG=0

DEVICE_MODELS=$(cd devices > /dev/null; ls -d */ | xargs | sed 's/\///g')

USAGE="Usage:\n\
        $(basename "$0") <device_model>\n\
        -h: displays this help message.\n\
        Positional Arguments:\n\
                <device_model>: which device model code to use.\n\
                        Acceptable values are: $DEVICE_MODELS"

# reads options:
while getopts "hd" flag
do
        case "$flag" in
                d)
                        DEBUG=1
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
fi

pinstates_file="devices/${DEVICE_MODEL}/device_files/pinstates.py"
delay_test_file="devices/${DEVICE_MODEL}/device_files/main.py"
#echo "Running \`mpremote fs cp \"${pinstates_file}\" :pinstates.py && python conveyor.py\`."
mpremote a1 fs cp "${delay_test_file}" :main.py
mpremote a0 fs cp "${pinstates_file}" :pinstates.py
python conveyor.py

