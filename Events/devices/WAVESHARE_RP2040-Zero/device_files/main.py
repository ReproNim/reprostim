from machine import Pin
import time
p29 = Pin(29, Pin.OUT)
p29.value(0)


def send_debug_signal():
    p29.value(1)
    time.sleep(1)
    p29.value(0)
