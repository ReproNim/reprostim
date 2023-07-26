from machine import Pin
import time
power = Pin(7, Pin.OUT)
power.value(0)


def send_debug_signal():
    power.value(1)
    time.sleep(1)
    power.value(0)
