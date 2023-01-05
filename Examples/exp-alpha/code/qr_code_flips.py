import qrcode
from psychopy import visual, core, event, clock
import glob
import numpy as np
from time import time
import dbic
import sys
import os
import json
from datetime import datetime


logfn = sys.argv[1]
# logfn = "../data/{0}/run{1}_logfile.csv".format(acqNum, runNum)
if os.path.exists(logfn):
    raise RuntimeError(f"Log file {logfn} already exists")


def get_times():
    t = time()
    return t, datetime.fromtimestamp(t).astimezone().isoformat()


def mkrec(**kwargs):
    t, tstr = get_times()
    kwargs.update({
        "time": t,
        "time_formatted": tstr,
    })
    return kwargs

# print(json.dumps(mkrec(blah=123), indent=4))

f = open(logfn, "w")

def log(rec):
    f.write(json.dumps(rec).rstrip() + os.linesep)

log(mkrec(event="started"))

win = visual.Window(fullscr=True,screen=0)
win.mouseVisible = False # hides the mouse pointer 

log(mkrec(event="started"))
message = visual.TextStim(win, text="""Waiting for scanner trigger.\nInstructions
        for Participant...""")
message.draw()

fixation = visual.TextStim(win, text='+')
reproinMessage = visual.TextStim(win, text="", pos=(0, -.7),
        height=.05)

win.flip()


fixation.draw()  # Change properties of existing stim
win.flip()

spd = 0.500 # Stimulus Presentation Duration
soa = 6.000 # Stimulus Onset Asynchrony
ntrials = 30
iwt = 5 # Initial Wait Time between scanner trigger and first stimulus

stim_images = []
stim_names = []

clk = clock.Clock()
for acqNum in range(ntrials):

    rec = mkrec(
        event="trigger",
        acqNum=acqNum
    )

    print("Waiting for trigger pulse ... or key stroke '5'")
    keys = event.waitKeys(maxWait=120) # keyList=['5'])
    rec['keys'] = keys
    qr = visual.ImageStim(win,
                          qrcode.make(json.dumps(rec)),
                          pos=(0, 0)
                          )
    qr.size = qr.size * 3
    qr.draw()
    win.flip()
    tflip, tflip_str = get_times()
    rec['time_flip'] = tflip
    rec['time_flip_formatted'] = tflip_str
    log(rec)

    win.flip()
    fixation.draw()
    if 'q' in keys:
        break

f.close()