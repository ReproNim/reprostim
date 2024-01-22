import select
import os
from mpremote import transport_serial
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
	run_listener = True
	while run_listener:
		events = poll.poll(-1)
		for file in events:
			line = pyb.serial.readline()
			mytime = time()
			#try:
			#	rec = eval(line)
			#except SyntaxError:
			#	pass
			#else:
			#	rec["client_time"] = mytime
			#	yield rec
			try:
				rec = eval(line)
			except SyntaxError:
				print(f"Got a syntax error in the line: {line}")
				pass
			else:
				try:
					rec["client_time"] = mytime
				except TypeError:
					if rec == "KILLLISTENER":
						run_listener = False
					else:
						yield rec
				else:
					yield rec



def no_listen(command, rt_devicenode="/dev/ttyACM1"):
	pyb_debug = transport_serial.SerialTransport(rt_devicenode, 115200)
	pyb_debug.enter_raw_repl()
	result = pyb_debug.exec_raw_no_follow(command)



