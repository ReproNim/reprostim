from mpremote import pyboard
from .listeners import listen

def check_roundtripper(devicenode):
	pyb = pyboard.Pyboard(devicenode, 115200)
	#listen('import roundtripper; roundtripper.selfreport()', pyb)
	for message in listen('import roundtripper; roundtripper.selfreport()', pyb):
		print(message)
