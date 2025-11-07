from psychopy import core, event, logging, visual
from psychopy_mri_emulator import launchScan

from reprostim.qr.psychopy import EventType, QrCode, QrStim, QrConfig
from reprostim.audio.audiocodes import AudioCodec

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
win = visual.Window([800, 600], units="pix", fullscr=False)

# Create a global clock to sync
globalClock = core.Clock()

# MRI scanner settings
MR_settings = {
    "TR": 2.0,  # time between volumes (sec)
    "volumes": 5,  # number of volumes to simulate
    "sync": "5",  # key representing scanner pulse
    "skip": 0,
    "sound": False,
}

# Custom QR code config wih audio codes enabled
qr_config = QrConfig(
    audio_enabled=True,
    audio_codec=AudioCodec.NFE,
    audio_volume=0.61,
    audio_data_field="seq",
    audio_sample_rate=44100,
    scale=0.5,
    padding=30,
    align="right-bottom",
)

# Create and draw sample fixation cross
fix = visual.TextStim(win, text="+", pos=(0, 0))
fix.draw()
win.flip()

logging.info("Starting fMRI scan emulator in test interval mode with audio")

show_qr(EventType.SESSION_START, win, fix, qr_config)

core.wait(1)

seq = 0
# Wait for first sync pulse (Test mode will generate them automatically)
seq += launchScan(win, MR_settings, globalClock=globalClock, mode="Test", log=True)
logging.info(f"Pulse[0], initial detected at {globalClock.getTime():.3f} sec")


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

# Display a QR code indicating the end of the session
show_qr(EventType.SESSION_END, win, fix, qr_config)

logging.info("Done.")
win.close()
core.quit()
