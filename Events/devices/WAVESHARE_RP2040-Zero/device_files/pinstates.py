from time import time
import utime
import machine

def report():
    """
    Monitor state changes on selected pins.

    Notes
    -----
    * As extant devices commonly have megahertz-range clock bounds, we use microsecond timings.
    """

    mypin = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_DOWN)
    i = 0
    priort = None
    priort_ = None
    priorv = None
    while True:
        i += 1
        t = utime.ticks_us()
        # Paranoid check to see if clock goes forward:
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
            #yield {"us": t, "persec": ipersec, "value": value, "reason": report_reason}
            print(repr({"us": t, "persec": ipersec, "value": value, "reason": report_reason}))
            #print(repr(value))
            priori = i
            priort = t
            priorv = value
