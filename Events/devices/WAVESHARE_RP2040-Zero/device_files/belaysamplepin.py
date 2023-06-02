import argparse
import time

import belay

parser = argparse.ArgumentParser()
parser.add_argument("--port", "-p", default="/dev/ttyUSB0")
args = parser.parse_args()

device = belay.Device(args.port)

@device.task
def sample():
    # import led
    # import json
    # led.cycle()

    import utime
    # import machine
    mypin = Pin(0, machine.Pin.IN)
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
            #print(json.dumps({"ms": t, "persec": ipersec, "value": value}))
            yield {"ms": t, "persec": ipersec, "value": value}
            priori = i
            priort = t


for s in sample():
    print(s)
