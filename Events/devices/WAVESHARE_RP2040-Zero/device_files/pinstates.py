from time import time
import utime
import machine
from machine import Pin
import json
import gc


def callback(p):
    """
    Report pin state change, while checking the current value.

    Parameters
    ----------
    p: machine.Pin
        A `machine.Pin` object.

    Notes
    -----
    1. Callback functions only support one parameter, which is a Pin object, we cannot pass other arguments via the callback interface.
    2. We do manual garbage collection, to ensure homogeneous callback durations, this may not be needed.
    """
    t_s0 = utime.ticks_us()
    cur_value = p.value()
    # Software debouncer, might not be needed:
    bounce = False
    while utime.ticks_us() - t_s0 < 200 and not bounce:
        if p.value() != cur_value:
            bounce = True
    if not bounce:
        t_s1 = utime.ticks_us()
        message={
            "callback_duration_us": t_s1 - t_s0,
            "us": t_s1,
            "pin_str": str(p),
            "state": cur_value}
        print(json.dumps(message))
        gc.collect()

def dry_test():
    return None

def report(
    pins=[0,1,2,3,4,5,6,7,8,9,10],
    debug_pin=29,
    ):
    """
    Monitor state changes on selected pins.

    Parameters
    ----------
    pins: list of int, optional
        Numerical values of pins for which the state will be reported.

    Notes
    -----
    * As extant devices commonly have megahertz-range clock bounds, we use microsecond timings.
    """

    # Pull-down pin will be 0 unless under voltage.
    debug_pin = machine.Pin(debug_pin, machine.Pin.IN, machine.Pin.PULL_DOWN)
    debug_pin.irq(trigger=Pin.IRQ_RISING, handler=callback)

    pins = [machine.Pin(i, machine.Pin.IN, machine.Pin.PULL_DOWN) for i in pins]
    [ipin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=callback) for ipin in pins]

    while True:
        pass
