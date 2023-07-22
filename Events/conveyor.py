import select
from mpremote import pyboard
from time import time

pyb = pyboard.Pyboard("/dev/ttyACM0", 115200)

def listen(command,
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
	print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
	print(command)
	print("BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB")
	#pyb = pyboard.Pyboard(port, 115200)
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


def listen_once(command, port="/dev/ttyACM0"):
	#pyb = pyboard.Pyboard(port, 115200)
	#poll = select.poll()
	#poll.register(pyb.serial, select.POLLIN)

	pyb.enter_raw_repl()
	result = pyb.exec_raw_no_follow(command)

	#events = poll.poll(-1)
	#for file in events:
		#print("DDDDDD")
		#result = pyb.serial.readline()
		#print("DDD")
		#try:
	return result
		#except SyntaxError:
			#pass

def timed_events(check_delay=True):
	dts = []
	dtbase = None
	ntrials = 0
	for message in listen('import pinstates; pinstates.report()'):
		print("EEEEEEEE")
		if check_delay:
			#t_c1 = time()
			#print("msg1")
			#t_s1 = message['us']
			#print("msg2.1")
			#dt1 = listen('import pinstates; pinstates.findDelay()')
			#print(dt1)
			#dt1 += t_s1
			#print("msg3")
			#t_c2 = time()
			#print("msg4")
			#dt2 = t_c2 - t_c1
			#print("server_times: " + str(dt1) + "\nclient_times: " + str(dt2))
			#pyb.eval("from machine import Pin; a = Pin(29, Pin.OUT); a.value(1)")	
			pyb.execfile("board_side.py")	
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
		if ntrials:
			if len(dts) >= ntrials:
				print(":(")
				break

def test_delay():
	t0 = time()
	pyb.enter_raw_repl()
	pyb.exec_raw_no_follow('import delay_test; delay_test.send_signal()')
	t1 = time()
	print(str((t1 - t0) * 1000) + " ms")


timed_events()
