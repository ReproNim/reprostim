from psychopy import event, visual, core, clock
import qrcode
import time

def waitTrigger(win, runNum, acqNum, qrDur=.05, qrPos=(-.5,-.5), qrSize=.2):


    data = {"acqNum": acqNum, 
            "runNum": runNum,
            "trialStart": time.time()
            }

    print("Waiting for trigger pulse ... or key stroke '5'")
    event.waitKeys(keyList=['5'])
    clk = clock.Clock()
    data["runStart"] = time.time()
    
    qr = visual.ImageStim(win, 
                        qrcode.make(str(data)),
                        pos=qrPos
                         )
    qr.size = qr.size*qrSize
    qr.draw()
    win.flip()
    core.wait(qrDur)
    return clk

def endRun(win, qrDur=.05, qrPos=(-.5,-.5), qrSize=.2):

    data = {"runEnd": time.time()}

    qr = visual.ImageStim(win, 
                    qrcode.make(str(data)),
                    pos=qrPos
                    )
    qr.size = qr.size*qrSize
    qr.draw()
    win.flip()
    core.wait(qrDur)
 
