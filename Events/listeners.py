import select
import os
from mpremote import pyboard
from time import time

def listen(command, pyb):
	"""
	Listen to reports from device.

	Notes
	-----
	* This could be set up as a global listener, though that might be overkill just for conveying stimulus events.
	* Using `-1` polling to disable timouts, we could use ipoll instead:
		https://docs.micropython.org/en/latest/library/select.html?highlight=poll#select.poll.ipoll
	"""


	poll = select.poll()
	poll.register(pyb.serial, select.POLLIN)

	pyb.enter_raw_repl()
	pyb.exec_raw_no_follow(command)
	while True:
		events = poll.poll(-1)
		for file in events:
			line = pyb.serial.readline()
			try:
				yield eval(line)
			except SyntaxError:
				pass


def no_listen(command):
	pyb_debug = pyboard.Pyboard("/dev/ttyACM1", 115200)
	pyb_debug.enter_raw_repl()
	result = pyb_debug.exec_raw_no_follow(command)



