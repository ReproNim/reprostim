import csv
import select
import os
from datetime import datetime
from mpremote import pyboard
from time import time
from .listeners import listen

# This should pobably be here
pyb = pyboard.Pyboard("/dev/ttyACM0", 115200)
tz = datetime.now().astimezone().tzinfo

def timed_events(
	log_file="/tmp/conveyor.csv",
	check_delay=False,
	report=True,
	):
	if check_delay:
		try:
			from .listeners import no_listen
		except pyboard.PyboardError:
			print("❌ Only one board is connected, live roundtrip delay testing will be disabled by default.")
			check_delay = False
		else:
			print("Live roundtrip delay is enabled.")
	else:
		print("Live roundtrip delay is disabled.")

	dts = []
	messages = []
	base_dt = None
	print("Starting to listen for events...")
	msg_id = 0
	pending_message = False
	with open(log_file,'w') as f:
		writer = None
		for message in listen('import pinstates; pinstates.report()', pyb):
			client_time = datetime.fromtimestamp(message['client_time'])
			message['client_time_iso'] = client_time.replace(tzinfo=tz).isoformat()
			if message['pin'] == 7:
				if not check_delay:
					print('WARNING: pin 7 is a debugging pin used to check delays, but you are not in debugging mode. What happened?')
				# Failsafe, the device function should not report drop debug events.
				#if message['state'] == 0:
				#	continue
				messages[-1]["roundtrip_delay"] = message["client_time"] - t_c0
				writer = handle_message(messages[-1], f, writer=writer, report=report)
				pending_message = False
			elif pending_message:
				writer = handle_message(pending_message, f, writer=writer, report=report)
				pending_message = False
			else:
				message['callback_duration'] = message['callback_duration_us']/1e6
				message['server_time'] = message.pop('us')/1e6
				dt = message['client_time'] - message['server_time']
				if base_dt is None:
					base_dt = dt
					dt = 0
				else:
					dt = dt-base_dt
				dts.append(dt)
				message["base_dt"] = base_dt
				message["relative_dt"] = dt
				message["roundtrip_delay"] = None
				msg_id += 1
				message["id"] = msg_id
				message["mean relative dt"]= sum(dts) / len(dts)
				messages.append(message)
				if check_delay:
					t_c0 = time()
					no_listen('import main; main.send_debug_signal()')
					pending_message = message
				else:
					writer = handle_message(message, f, writer=writer, report=report)

def handle_message(my_message, f,
	writer=None,
	report=False,
	):
	if report:
		print(my_message)
	if not writer:
		writer = csv.DictWriter(f, my_message.keys())
		writer.writeheader()
	writer.writerow(my_message)
	f.flush()
	return writer

def test_delay_dry():
	t0 = time()
	pyb.enter_raw_repl()
	pyb.exec_raw_no_follow('import pinstates; pinstates.dry_test()')
	t1 = time()
	print(f'Single board delay is {t1 - t0} seconds.')


def convey(log_file="/tmp/conveyor.csv", check_delay=False):
	test_delay_dry()
	timed_events(log_file=log_file, check_delay=check_delay)
