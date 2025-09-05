from psychopy_mri_emulator import launchScan
from psychopy import visual, core, event, logging

logging.console.setLevel(logging.INFO)

# Create a window
win = visual.Window([800, 600], fullscr=False)

# Create a global clock to sync
globalClock = core.Clock()

# MRI scanner settings
MR_settings = {
    'TR': 0.2,       # time between volumes (sec)
    'volumes': 5,    # number of volumes to simulate
    'sync': '5',     # key representing scanner pulse
    'skip': 0,
    'sound': False
}

logging.info("Starting fMRI scan emulator in scan event mode")

seq = 0
# Wait for first sync pulse
seq += launchScan(win, MR_settings, globalClock=globalClock,
           mode='Scan',  log=True)
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