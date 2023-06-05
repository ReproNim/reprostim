import select
from mpremote import pyboard
from time import time

def monitor(command,
	port="/dev/ttyACM0",
	):
	"""
	Listen to reports from device.

	Notes
	-----
	* This could be set up as a global listener, though that might be overkill just for conveying stimulus events.
	* Using `-1` polling to disable timouts, we could use ipoll instead:
		https://docs.micropython.org/en/latest/library/select.html?highlight=poll#select.poll.ipoll
	"""
	pyb = pyboard.Pyboard(port, 115200)
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


def timed_events():
	dts = []
	dtbase = None
	ntrials = 0
	for message in monitor('import pinstates; pinstates.report()'):
		t = time()
		us = message['us']/1e6
		dt = t - us
		if dtbase is None:
			dtbase = dt
			print(f"Base dt={dt}")
		dts.append(dt)
		message["time"] = t
		meandt = sum(dts) / len(dts)
		maxdt = max(abs(dt - meandt) for dt in dts)
		print(message, f"max(dt)={maxdt}")
		if ntrials:
			if len(dts) >= ntrials:
				break

timed_events()
