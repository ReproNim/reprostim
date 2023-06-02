#!/bin/bash
myboard="${MEDIA_PATH:-/run/media}/$(whoami)/RPI-RP2"

if [ ! -d "$myboard" ]; then
	echo "❌$myboard does not exist."
	echo "	Firmware installation requires the device to be connected in mass storage mode."
	echo "	You can accomplish this by:"
	echo "		1. disconnecting the device"
	echo "		2. holding down the “BOOT” button"
	echo "		3. re-connecting the device, and"
	echo "		4. only releasing the button after it is connected."
	echo "	After you do that, just re-run this script"
	exit 1
fi

pushd ..
	./mpdl.py seeed_xiao_nrf52
popd
	umount ${myboard}
	sleep 2
	while ! $(mpremote fs ls &> /dev/null); do
		echo "The device has not auto-connected, please press the “RESET”button on the device once to continue."
		sleep 5
	done
	mpremote fs cp device_files/* :
	mpremote reset
