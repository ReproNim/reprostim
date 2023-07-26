import machine
import time
power = machine.Pin(7, machine.Pin.OUT)
power.value(0)

def send_debug_signal():
	power.value(1)
	time.sleep(1)
	power.value(0)
