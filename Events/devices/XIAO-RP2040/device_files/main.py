from machine import Pin
import time
debug_pin = Pin(1, Pin.OUT)
debug_pin.value(0)

# Pls check whether our roundtrip delay is larger if the Pin is defined in the function as opposed to global scope.
def send_debug_signal():
    debug_pin.value(1)
    time.sleep(0.001)
    debug_pin.value(0)

def send_predefined_event(mypin=0, myduration=1):
    event_pin = Pin(mypin, Pin.OUT)
    event_pin.value(1)
    time.sleep(myduration)
    event_pin.value(0)
