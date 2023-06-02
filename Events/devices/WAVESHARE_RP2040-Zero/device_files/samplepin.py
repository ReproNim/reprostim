# import led
import json
# led.cycle()

import utime
import machine
mypin = machine.Pin(0, machine.Pin.IN)
i = 0
priort = 0
while True: 
    i += 1
    t = utime.ticks_us()
    if priort == 0:
        priort = t
        priori = i
    value = mypin.value()
    if t - priort >= 1000000:
        ipersec = (i - priori) / (float(t-priort) / 1000000)
        print(json.dumps({"ms": t, "persec": ipersec, "value": value}))
        priori = i
        priort = t
