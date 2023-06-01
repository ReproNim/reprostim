import machine
power = machine.Pin(11,machine.Pin.OUT)
power.value(1)

import led

led.cycle()
