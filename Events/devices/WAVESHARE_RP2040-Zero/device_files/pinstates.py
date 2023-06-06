from time import time
import utime
import machine

def report(precision=1e3):
    """
    Monitor state changes on selected pins.

    Parameters
    ----------
    precision: int, optional
        After how many microseconds to record a precision.
        This can be used to generate precision warnings, e.g:
            - `precision=1e6` will log a warning if the current polling timestamp is more than 1s after the prior one.
            - `precision=1e2` will log a warning if the current polling timestamp is more than 100μs after the prior one.

    Notes
    -----
    * As extant devices commonly have megahertz-range clock bounds, we use microsecond timings.
    * Preciossion is controlled via the `timeout` parameter and is by default 1ms.
    """

    # Pull-down pin will be 0 unless under voltage.
    mypin = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_DOWN)
    prior_value = 0

    prior_t = utime.ticks_us()
    i = 0
    while True:
        value = mypin.value()
        t = utime.ticks_us()
        # Has time stopped?
        assert t > prior_t

        # Generate report:
        dt = t - prior_t
        timeout = dt > precision
        change = value != prior_value
        if change or timeout:
            cycle_frequency = 1 / (dt / 1e6)
            message={
                "us": t,
                "cycle_frequency": cycle_frequency,
                "cycle": i,
                "pin_value": value,
                "change": change,
                "timeout": timeout,
                }
            # Caveman-style because this is its own interpreter:
            print(repr(message))
        prior_t = t
        prior_value = value
        i += 1
