#!/usr/bin/env python3

import argparse
import requests
from bs4 import BeautifulSoup

URL_FORMAT="https://micropython.org/download/{device}/"

def _get_firmware_links(device,
	extension="uf2",
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
	return [my_url + link["href"] for link in links if link["href"].endswith(f".{extension}")]


def _download(firmware_links):
	"""
	Iterate through all links in firmware_links and download the first link.

	Parameters
	----------
	firmware_links: str
		List of strings which are HTTP links pointing to micropython firmware links.
	"""

	# Get filename by splitting the last url.
	firmware_link = firmware_links[0]
	filename = firmware_link.split("/")[-1]

	print(f"Selected link: `{firmware_link}`:")
	request = requests.get(firmware_link, stream=True)

	with open(filename, "wb") as f:
		for chunk in request.iter_content(chunk_size=1024 * 1024):
			if chunk:
				f.write(chunk)

	print(f"	✔️ `{filename}` downloaded.\n")


if __name__ == "__main__":
	argparser = argparse.ArgumentParser(
		prog="mpdl.py",
		description="Download the most recent (currently just the first) firmware link from the webpage.",
		epilog="Example: ./mpdl.py https://micropython.org/download/rp2-pico/ uf2",
	)

	argparser.add_argument("device",
		help="Device name as known to the micropython website.",
	)
	argparser.add_argument("extension",
		help="Desired extension of the firmware.",
	)
	argparser.add_argument("-u", "--url-format",
		help="Desired extension of the firmware.",
		default=URL_FORMAT,
	)
	args = argparser.parse_args()

	firmware_links = _get_firmware_links(args.device,
		extension=args.extension,
		url_format=args.url_format,
	)
	_download(firmware_links)
