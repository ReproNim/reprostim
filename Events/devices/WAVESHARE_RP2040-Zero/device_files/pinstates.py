from time import time
import utime
import machine

def report(timeout=1000):
    """
    Monitor state changes on selected pins.

    Parameters
    ----------
    timeout: int, optional
        After how many microseconds to record a timeout.
        This can be used to generate precision warnings, e.g:
            - `timeout=1000` will log a warning if the current polling timestamp is more than 1ms after the prior one.
            - `timeout=100` will log a warning if the current polling timestamp is more than 100μs after the prior one.

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
        timeout =  False
        change = False
        dt = t - prior_t
        if dt >= timeout:
            timeout = True
        if value != prior_value:
            change = True
        if change or timeout:
            cycle_period = 1 / (dt / 1e6)
            # Caveman-style because this is its own interpreter:
            notification={
                "us": t,
                "cycle_frequency": cycle_frequency,
                "cycle": i,
                "pin_value": value,
                "change": change,
                "timeout": timeout,
                }
            print(repr(notification))
        prior_t = t
        prior_value = value
        i += 1
