import select
from mpremote import pyboard
from time import time

pyb = pyboard.Pyboard("/dev/ttyACM0", 115200)
pyb_debug = pyboard.Pyboard("/dev/ttyACM1", 115200)

def listen(command):
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
	pyb_debug.enter_raw_repl()
	result = pyb_debug.exec_raw_no_follow(command)

def timed_events(check_delay=True):
	dts = []
	dtbase = None
	ntrials = 0
	for message in listen('import pinstates; pinstates.report()'):
		if message['pin'] == 29:
			t_c1 = time()
			if not check_delay:
				print('WARNING: pin 29 is a debugging pin used to check delays, but you are not in debugging mode. What happened?')
			if message['state'] == 0:
				continue
			roundtrip_delay = t_c1 - t_c0
			print(f'DEBUG: Roundtrip delay is {roundtrip_delay}.')
		else:
			message['callback_duration'] = message['callback_duration_us']/1e6
			message['client_time'] = time()
			message['server_time'] = message.pop('us')/1e6
			dt = message['client_time'] - message['server_time']
			if dtbase is None:
				dtbase = dt
				print(f"Base dt={dt}")
				dt = 0
			else:
				dt = dt-dtbase
			dts.append(dt)
			meandt = sum(dts) / len(dts)
			print(message, f"— with dt={dt} and mean(dt)={meandt}")
			if check_delay:
				t_c0 = time()
				no_listen('import main; main.send_debug_signal()')

def test_delay_dry():
	t0 = time()
	pyb.enter_raw_repl()
	pyb.exec_raw_no_follow('import pinstates; pinstates.dry_test()')
	t1 = time()
	print(f'Single board delay is {t1 - t0}.')


timed_events()
