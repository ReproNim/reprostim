from psychopy import core, event, logging, visual
from psychopy_mri_emulator import launchScan

from reprostim.qr.psychopy import EventType, QrCode, QrStim

logging.console.setLevel(logging.INFO)


# Create a window
win = visual.Window([800, 600], units="pix", fullscr=False)

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

logging.info("Starting fMRI scan emulator in test interval mode")

# Display a QR code indicating the start of the session
qr = QrStim(win, QrCode(EventType.SESSION_START))
qr.draw()
win.flip()
# wait for its duration
qr.wait()
win.flip()

core.wait(2)

seq = 0
# Wait for first sync pulse (Test mode will generate them automatically)
seq += launchScan(win, MR_settings, globalClock=globalClock, mode="Test", log=True)
logging.info(f"Pulse[0], initial detected at {globalClock.getTime():.3f} sec")


# Main loop to react to pulses
while True:
    keys = event.getKeys()
    if MR_settings["sync"] in keys:
        logging.info(f"Pulse[{seq}] detected at {globalClock.getTime():.3f} sec")
        seq += 1
        if seq >= MR_settings["volumes"]:
            logging.info("All volumes acquired.")
            break
    if "escape" in keys:
        logging.info("Experiment terminated by user (Escape pressed)")
        break

# Display a QR code indicating the end of the session
qr = QrStim(win, QrCode(EventType.SESSION_END))
qr.draw()
win.flip()
# wait for its duration
qr.wait()
win.flip()

logging.info("Done.")
win.close()
core.quit()
