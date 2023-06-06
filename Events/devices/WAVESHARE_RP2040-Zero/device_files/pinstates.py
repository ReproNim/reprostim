from time import time
import utime
import machine

def report(pins=[0,1,2,3,4,5,6,7,8,9,10],
    precision=1e3,
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
    * Preciossion is controlled via the `timeout` parameter and is by default 1ms.
    """

    # Pull-down pin will be 0 unless under voltage.
    pins = [machine.Pin(i, machine.Pin.IN, machine.Pin.PULL_DOWN) for i in pins]
    prior_values = values = [ipin.value() for ipin in pins]

    prior_t = utime.ticks_us()
    i = 0
    while True:
        values = [ipin.value() for ipin in pins]
        t = utime.ticks_us()
        # Has time stopped?
        assert t > prior_t

        # Generate report:
        dt = t - prior_t
        timeout = dt > precision
        # Move a and b around to see what segments of the code take the most time
        a = utime.ticks_us()
        change = not all(i == j for i,j in zip(values, prior_values))
        b = utime.ticks_us()
        if change or timeout:
            cycle_frequency = 1 / (dt / 1e6)
            message={
                "ab": b-a,
                "us": t,
                "mydt": dt,
                "cycle_frequency": cycle_frequency,
                "cycle": i,
                "pin_values": values,
                "change": change,
                "timeout": timeout,
                }
            # Caveman-style because this is its own interpreter:
            print(repr(message))
        prior_t = t
        prior_values = values
        i += 1
