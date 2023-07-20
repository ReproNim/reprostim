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
    pin_str = str(p)
    pin_num = pin_str[8:len(pin_str) - 26]
    pin_int = int(pin_num)
    t_s1 = utime.ticks_us()
    message={
        "callback_duration_us": t_s1 - t_s0,
        "us": t_s1,
        "pin": pin_int,
        "state": p.value()}
    print(json.dumps(message))
    gc.collect()


def findDelay():
    t_s2 = utime.ticks_us()
    return t_s2


def report(pins=[0,1,2,3,4,5,6,7,8,9,10],
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
    pins = [machine.Pin(i, machine.Pin.IN, machine.Pin.PULL_DOWN) for i in pins]
    [ipin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=callback) for ipin in pins]

    while True:
        pass
    #prior_values = values = [ipin.value() for ipin in pins]

    #prior_t = utime.ticks_us()

    #gc.disable()

    #while True:
    #    # Move a and b around to see what segments of the code take the most time
    #    a = utime.ticks_us()
    #    values = [ipin.value() for ipin in pins]
    #    b = utime.ticks_us()
    #    t = utime.ticks_us()
    #    # Has time stopped?
    #    assert t > prior_t

    #    # Generate report:
    #    dt = t - prior_t
    #    timeout = dt > precision
    #    change = not all(i == j for i,j in zip(values, prior_values))
    #    if change or timeout:
    #        message={
    #            "ab": b-a,
    #            "us": t,
    #            "cycle_us": dt,
    #            "pin_values": values,
    #            "change": change,
    #            "timeout": timeout,
    #            }
    #        # Caveman-style because this is its own interpreter:
    #        print(repr(message))
    #    prior_t = t
    #    prior_values = values
    #    gc.collect()
