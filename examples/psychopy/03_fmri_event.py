from psychopy import core, event, logging, visual
from psychopy_mri_emulator import launchScan

from reprostim.qr.psychopy import EventType, QrCode, QrConfig, QrStim

logging.console.setLevel(logging.INFO)


def show_qr(event, win, fix, qr_config, **kwargs):
    # draw a QR code with given parameters
    qr = QrStim(win, QrCode(event, **kwargs), qr_config)
    fix.draw()
    qr.draw()
    win.flip()
    # wait for its duration
    qr.wait()

    # restore fixation cross
    fix.draw()
    win.flip()


# Create a window
win = visual.Window([800, 600], fullscr=False)

# Custom QR code config
qr_config = QrConfig(
    scale=0.5,
    padding=30,
    align="right-bottom",
)


# Create a global clock to sync
globalClock = core.Clock()

# MRI scanner settings
MR_settings = {
    "TR": 0.2,  # time between volumes (sec)
    "volumes": 5,  # number of volumes to simulate
    "sync": "5",  # key representing scanner pulse
    "skip": 0,
    "sound": False,
}

# Create and draw sample fixation cross
fix = visual.TextStim(win, text="+", pos=(0, 0))
fix.draw()
win.flip()

logging.info("Starting fMRI scan emulator in scan event mode")

show_qr(EventType.SESSION_START, win, fix, qr_config)

seq = 0
# Wait for first sync pulse
seq += launchScan(win, MR_settings, globalClock=globalClock, mode="Scan", log=True)
logging.info(f"Pulse[0], initial detected at {globalClock.getTime():.3f} sec")

show_qr(
    EventType.MRI_TRIGGER_RECEIVED, win, fix, qr_config, seq=0, keys=MR_settings["sync"]
)

# Main loop to react to pulses
while True:
    keys = event.getKeys()
    if MR_settings["sync"] in keys:
        logging.info(f"Pulse[{seq}] detected at {globalClock.getTime():.3f} sec")
        show_qr(EventType.MRI_TRIGGER_RECEIVED, win, fix, qr_config, seq=seq, keys=keys)
        seq += 1
        if seq >= MR_settings["volumes"]:
            logging.info("All volumes acquired.")
            break
    if "escape" in keys:
        logging.info("Experiment terminated by user (Escape pressed)")
        break

show_qr(EventType.SESSION_END, win, fix, qr_config)

logging.info("Done.")
win.close()
core.quit()
