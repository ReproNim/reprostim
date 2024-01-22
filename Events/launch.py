from mpremote import transport_serial
from .listeners import listen

def check_roundtripper(devicenode):
	pyb = transport_serial.SerialTransport(devicenode, 115200)
	#listen('import roundtripper; roundtripper.selfreport()', pyb)
	for message in listen('import roundtripper; roundtripper.selfreport()', pyb):
		print(message)
