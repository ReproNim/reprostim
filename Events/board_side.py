from machine import Pin

# create an output pin on pin #0
p0 = Pin(29, Pin.OUT)

# set the value low then high
p0.value(1)
