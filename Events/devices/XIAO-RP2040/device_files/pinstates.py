from time import time
import utime
import machine
import gc

def report(pins=[0,1,2,3,4,6,7,26,27,28,29],
    precision=50000,
    ):
    """
    Monitor state changes on selected pins.

    Parameters
    ----------
    pins: list of int, optional
        Numerical values of pins for which the state will be reported.
    precision: int, optional
        Upper bound of cycle duration above which to issue a warning — in μs.
        This can be used to generate precision warnings, e.g:
            - `precision=1e6` will log a warning if the current polling timestamp is more than 1s after the prior one.
            - `precision=1e2` will log a warning if the current polling timestamp is more than 100μs after the prior one.

    Notes
    -----
    * As extant devices commonly have megahertz-range clock bounds, we use microsecond timings.
    * Precision is controlled via the `timeout` parameter and is by default 1ms.
    * This function uses explicit garbage collection.
        By default garbage is collected when memory is full, which increases the duration of specific loops.
        This makes incremental development work with respect to precision more difficult.
        By explicitly triggering it once per loop cycle, the time penalty is uniformly incurred.
    * The highest reliable precision of this function is 5400μs. Time expenditures are as follows:
        - value read-in: ~250μs
        - dictionary construction, repr, and print: ~800μs
        - garbage collection: ~3900μs
    """

    # Pull-down pin will be 0 unless under voltage.
    pins = [machine.Pin(i, machine.Pin.IN, machine.Pin.PULL_DOWN) for i in pins]
    prior_values = values = [ipin.value() for ipin in pins]

    prior_t = utime.ticks_us()

    gc.disable()

    while True:
        # Move a and b around to see what segments of the code take the most time
        a = utime.ticks_us()
        values = [ipin.value() for ipin in pins]
        b = utime.ticks_us()
        t = utime.ticks_us()
        # Has time stopped?
        assert t > prior_t

        # Generate report:
        dt = t - prior_t
        timeout = dt > precision
        change = not all(i == j for i,j in zip(values, prior_values))
        if change or timeout:
            message={
                "ab": b-a,
                "us": t,
                "cycle_us": dt,
                "pin_values": values,
                "change": change,
                "timeout": timeout,
                }
            # Caveman-style because this is its own interpreter:
            print(repr(message))
        prior_t = t
        prior_values = values
        gc.collect()
