from machine import Pin
import time
power = Pin(1, Pin.OUT)
power.value(0)

def send_debug_signal():
	power.value(1)
	time.sleep(1)
	power.value(0)

def send_predefined_event(mypin=0, myduration=1):
	power = Pin(mypin, Pin.OUT)
	power.value(1)
	time.sleep(myduration)
	power.value(0)
