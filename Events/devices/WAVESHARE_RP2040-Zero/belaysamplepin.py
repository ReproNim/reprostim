import argparse
from time import time

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
    priort = None
    priort_ = None
    priorv = None
    while True:
        i += 1
        t = utime.ticks_us()
        # just for paranoid check to see if clock goes forward
        if priort_:
            assert t > priort_
        priort_ = t
        if not priort:
            priort = t
            priori = i
        value = mypin.value()
        report_reason = None
        if t - priort >= 1000000:
            report_reason = 'timeout'
        if value != priorv:
            report_reason = 'change'
        if report_reason:
            ipersec = (i - priori) / (float(t-priort) / 1000000) if t!=priort else None
            #print(json.dumps({"ms": t, "persec": ipersec, "value": value}))
            yield {"us": t, "persec": ipersec, "value": value, "reason": report_reason}
            priori = i
            priort = t
            priorv = value


dts = []
dtbase = None
ntrials = 0
for s in sample():
    t = time()
    us = s['us']/1e6
    dt = t - us
    if dtbase is None:
        dtbase = dt
        print(f"Base dt={dt}")
    dts.append(dt)
    s["time"] = t
    meandt = sum(dts) / len(dts)
    maxdt = max(abs(dt - meandt) for dt in dts)
    print(s, f"max(dt)={maxdt}")
    if ntrials:
        if len(dts) >= ntrials:
            break
