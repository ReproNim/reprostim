from psychopy_mri_emulator import launchScan
from psychopy import visual, core, event, logging

logging.console.setLevel(logging.INFO)


# common functions
def generate_sim_responses(
    n_series: int = 3,
    pulses_per_series: int = 5,
    intra_pulse_delay: float = 0.2,
    inter_series_delay: float = 3.0,
    initial_delay: float = 2.0,
    key: str = '5'   # default MRI trigger key
):
    """
    Generate simResponses for PsychoPy's launchScan.

    Parameters
    ----------
    n_series : int
        Number of series (blocks of pulses).
    pulses_per_series : int
        Number of pulses in each series.
    intra_pulse_delay : float
        Delay between pulses within a series (seconds).
    inter_series_delay : float
        Delay between consecutive series (seconds).
    initial_delay : float
        Delay before the first series starts (seconds).
    key : str
        Key name to simulate (default '5', typical for scanner triggers).

    Returns
    -------
    list of (float, str)
        A list suitable for simResponses.
    """
    sim_responses = [(0.0, "0")]  # initial dummy response
    t = initial_delay

    for s in range(n_series):
        for p in range(pulses_per_series):
            sim_responses.append((t, key))
            t += intra_pulse_delay
        t += inter_series_delay  # pause before next series

    return sim_responses



# Create a window
win = visual.Window([800, 600], fullscr=False)

# Create a global clock to sync
globalClock = core.Clock()

# Generate simulated series parameters
n_series = 3
pulses_per_series = 5
intra_pulse_delay = 0.2
inter_series_delay = 3.0
initial_delay = 2.0
sim_responses = generate_sim_responses(n_series, pulses_per_series,
                                       intra_pulse_delay, inter_series_delay,
                                       initial_delay, key='5')
n_pulses = n_series * pulses_per_series

# MRI scanner settings
MR_settings = {
    'TR': 1000.0, # time between volumes (sec)
    'volumes': n_pulses,     # number of volumes to simulate
    'sync': '5',             # key representing scanner pulse
    'skip': n_pulses,
    'sound': False
}

logging.info("Starting fMRI scan emulator in test series mode")
logging.info(f"Simulating {n_series} series of {pulses_per_series} pulses each "
             f"({n_pulses} total)")
# logging.debug(f"simResponses: {sim_responses}")


seq = 0
# Wait for first sync pulse (Test mode will generate them automatically)
seq += launchScan(win, MR_settings, globalClock=globalClock,
           simResponses=sim_responses,
           mode='Test',  log=True)
logging.info(f"Pulse[0], initial detected at {globalClock.getTime():.3f} sec")

# Main loop to react to pulses
while True:
    keys = event.getKeys()
    if MR_settings['sync'] in keys:
        logging.info(f"Pulse[{seq}] detected at {globalClock.getTime():.3f} sec")
        seq += 1
        if seq >= MR_settings['volumes']:
            logging.info("All volumes acquired.")
            break
    if 'escape' in keys:
        logging.info("Experiment terminated by user (Escape pressed)")
        break

logging.info("Done.")
win.close()
core.quit()