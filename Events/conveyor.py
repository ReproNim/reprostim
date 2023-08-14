import select
import os
from mpremote import pyboard
from time import time
from .listeners import listen

# This should pobably be here
pyb = pyboard.Pyboard("/dev/ttyACM0", 115200)


CHECK_DELAY = True #temporary line for debugging


def timed_events(check_delay):
	print(check_delay)
	if check_delay:
		try:
			from .listeners import no_listen
		except pyboard.PyboardError:
			print("Only one board is connected, live roundtrip delay testing will be disabled by default.")
			check_delay = False
			print(check_delay)
	dts = []
	dtbase = None
	ntrials = 0
	for message in listen('import pinstates; pinstates.report()', pyb):
		if message['pin'] == 7:
			t_c1 = time()
			if not check_delay:
				print('WARNING: pin 7 is a debugging pin used to check delays, but you are not in debugging mode. What happened?')
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
	print(f'Single board delay is {t1 - t0} seconds.')


def main(CHECK_DELAY):
	test_delay_dry()
	timed_events(CHECK_DELAY)
