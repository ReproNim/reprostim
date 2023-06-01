#!/usr/bin/env python3

import argparse
import requests
import os
import getpass
import shutil
from bs4 import BeautifulSoup

URL_FORMAT="https://micropython.org/download/{device}/"
EXTENSION="uf2"
DESTINATION=f"/run/media/{getpass.getuser()}/RPI-RP2"

def _get_firmware_link(device,
	extension=EXTENSION,
	url_format=URL_FORMAT,
	):
	"""Get all href links that end with the given extension.

	Parameters
	----------
	device: str
		String specifying the device type as it is know to the micropython website, e.g. "rp2-pico".
		These strings are generally all-lowercase with dashes instead of spaces or underscores.
	extension: str, optional
		String specifying the desired format.
	url_format: str, optional
		Formattable string containing the string `{device}`, which serves as a template for device-specific firmware websites.
	"""
	my_url = url_format.format(device=device)
	request = requests.get(my_url)
	soup = BeautifulSoup(request.content, features="lxml")

	# Filter website links by extension.
	links = soup.findAll("a")
	firmware_links = [my_url + link["href"] for link in links if link["href"].endswith(f".{extension}")]

	# Get filename by splitting the last url.
	firmware_link = firmware_links[0]

	return firmware_link


def _download(firmware_links):
	"""
	Iterate through all links in firmware_links and download the first link.

	Parameters
	----------
	firmware_links: str
		List of strings which are HTTP links pointing to micropython firmware links.
	"""

	request = requests.get(firmware_link, stream=True)

	filename = firmware_link.split("/")[-1]
	firmware_path = os.path.join("/tmp", filename)
	with open(firmware_path, "wb") as f:
		for chunk in request.iter_content(chunk_size=1024 * 1024):
			if chunk:
				f.write(chunk)

	return firmware_path


def _install(firmware_path,
	destination_dir=DESTINATION,
	):
	if os.path.isdir(destination_dir):
		installed_file = shutil.copy(firmware_path, destination_dir)
		return installed_file
	else:
		print(f"❌{destination_dir} does not exist."\
			"Firmware installation requires the device to be connected in mass storage mode."
			"You can accomplish this by:"
         		"1. disconnecting the device"
         		"2. holding down the “BOOT” button"
         		"3. re-connecting the device, and"
         		"4. only releasing the button after it is connected."
			"After you do that, just re-run this script"
		)
		raise ValueError

if __name__ == "__main__":
	argparser = argparse.ArgumentParser(
		prog="mpdl.py",
		description="Download the most recent (currently just the first) firmware link from the webpage.",
		epilog="Example: ./mpdl.py https://micropython.org/download/rp2-pico/ uf2",
	)

	argparser.add_argument("device",
		help="Device name as known to the micropython website.",
	)
	argparser.add_argument("-e", "--extension",
		help="Desired extension of the firmware.",
		default=EXTENSION,
	)
	argparser.add_argument("-u", "--url-format",
		help="URL format for querying download links",
		default=URL_FORMAT,
	)
	argparser.add_argument("-d", "--destination",
		help="Destination directory under which to install firmware.",
		default=DESTINATION,
	)
	args = argparser.parse_args()

	firmware_link = _get_firmware_link(args.device,
		extension=args.extension,
		url_format=args.url_format,
	)
	print(f"✔️ Selected link: `{firmware_link}`.")
	firmware_path = _download(firmware_link)
	print(f"✔️ Downloaded micropython firmware under: `{firmware_path}`.")
	installed_file =_install(firmware_path, args.destination)
	print(f"✔️ Installed micropython firmware under: `{installed_file}`.")
