import csv
import select
import os
from datetime import datetime
from mpremote import pyboard
from time import time
from .listeners import listen

tz = datetime.now().astimezone().tzinfo

def load_pin_assignment(
	in_file='pin_assignments.csv',
	device_model='XIAO-RP2040',
	output_mode='DB-25P',
	):
	import csv

	with open(in_file, 'r') as f:
		reader = csv.DictReader(f)
		pin_dict = list(reader)

	board_pins = [i[device_model] for i in pin_dict]
	outputs = [i[output_mode] for i in pin_dict]

	pin_assignment = dict(zip(board_pins, outputs))

	return pin_assignment


def pin_parse(pin_str):
	import re

	pin_str = pin_str[8:10]
	numbers_only = re.compile(r'[^\d.]+')
	pin = numbers_only.sub('', pin_str)
	return pin

def timed_events(
	log_file="/tmp/conveyor.csv",
	check_delay=False,
	devicenode="/dev/ttyACM0",
	rt_devicenode="/dev/ttyACM1",
	report=True,
	pin_assignment=None,
	):
	pyb = pyboard.Pyboard(devicenode, 115200)
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
			message['pin'] = pin_parse(message['pin_str'])
			if pin_assignment[message['pin']] == 'DEBUG':
				if not check_delay:
					print(f'WARNING: pin {message["pin"]} is a debugging pin used to check delays, but you are not in debugging mode. What happened?')
				else:
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
				message.pop('pin_str', None)
				message["action"] = pin_assignment[message['pin']]
				message["base_dt"] = base_dt
				message["relative_dt"] = dt
				message["roundtrip_delay"] = None
				msg_id += 1
				message["id"] = msg_id
				message["mean relative dt"]= sum(dts) / len(dts)
				messages.append(message)
				if check_delay:
					t_c0 = time()
					no_listen('import main; main.send_debug_signal()', rt_devicenode=rt_devicenode)
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

def test_delay_dry(devicenode="/dev/ttyACM0"):
	pyb = pyboard.Pyboard(devicenode, 115200)
	t0 = time()
	pyb.enter_raw_repl()
	pyb.exec_raw_no_follow('import pinstates; pinstates.dry_test()')
	t1 = time()
	print(f'Single board delay is {t1 - t0} seconds.')


def convey(
		devicenode="/dev/ttyACM0",
		rt_devicenode="/dev/ttyACM1",
		log_file="/tmp/conveyor.csv",
		check_delay=False,
		device_model='XIAO-RP2040',
		output_mode='DB-25P',
		):
	test_delay_dry()
	pin_assignment = load_pin_assignment(
			device_model=device_model,
			output_mode=output_mode,
			)
	timed_events(
			devicenode=devicenode,
			rt_devicenode=rt_devicenode,
			log_file=log_file,
			check_delay=check_delay,
			pin_assignment=pin_assignment,
			)
