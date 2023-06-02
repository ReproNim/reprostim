mytempdir="/tmp/Rp2-pico-w-firmware-$(date +%s)"
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


mkdir -p "${mytempdir}"
pushd "${mytempdir}"
	wget https://www.waveshare.com/w/upload/b/b4/Rp2-pico-w-20230219-unstable-v1.19.1.uf2.zip
	unzip *.zip
	cp *uf2 "${myboard}/"
popd
	umount ${myboard}
	sleep 2
	mpremote fs cp device_files/* :
	mpremote reset
