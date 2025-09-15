import time

import qrcode
from psychopy import clock, core, event, visual


def waitTrigger(win, runNum, acqNum, qrDur=0.05, qrPos=(-0.5, -0.5), qrSize=0.2):

    data = {"acqNum": acqNum, "runNum": runNum, "trialStart": time.time()}

    print("Waiting for trigger pulse ... or key stroke '5'")
    event.waitKeys(keyList=["5"])
    clk = clock.Clock()
    data["runStart"] = time.time()

    qr = visual.ImageStim(win, qrcode.make(str(data)), pos=qrPos)
    qr.size = qr.size * qrSize
    qr.draw()
    win.flip()
    core.wait(qrDur)
    return clk


def endRun(win, qrDur=0.05, qrPos=(-0.5, -0.5), qrSize=0.2):

    data = {"runEnd": time.time()}

    qr = visual.ImageStim(win, qrcode.make(str(data)), pos=qrPos)
    qr.size = qr.size * qrSize
    qr.draw()
    win.flip()
    core.wait(qrDur)
