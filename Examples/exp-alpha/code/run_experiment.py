
from psychopy import visual, core, event, clock
import glob
import numpy as np
from time import time
import dbic
import sys
import os


acqNum = sys.argv[1]
runNum = int(sys.argv[2])

try: 
    os.mkdir("../data/{}".format(acqNum))
except:
    pass

logfn = "../data/{0}/run{1}_logfile.csv".format(acqNum, runNum)
f = open(logfn,"w")
f.write("{}\tStart Experiment\n".format(time()))
f.close()

def log(messg):
    f = open(logfn,"a")
    f.write("{}\t{}\n".format(time(),messg))
    f.close()



win = visual.Window(fullscr=True,screen=0)
win.mouseVisible = False # hides the mouse pointer 

message = visual.TextStim(win, text="""Waiting for scanner trigger.\nInstructions
        for Participant...""")
message.draw()

fixation = visual.TextStim(win, text='+')
reproinMessage = visual.TextStim(win, text="", pos=(0, -.7),
        height=.05)


win.flip()




########### wait for trigger here
#
c = dbic.waitTrigger(win, runNum, acqNum)
#################################





fixation.draw()  # Change properties of existing stim
win.flip()

spd = 0.500 # Stimulus Presentation Duration
soa = 6.000 # Stimulus Onset Asynchrony
ntrials = 30
iwt = 5 # Initial Wait Time between scanner trigger and first stimulus

stim_list = glob.glob("../stim/tarantula/*")
stim_list = stim_list + glob.glob("../stim/scorpion/*")
np.random.shuffle(stim_list)

stim_images = []
stim_names = []


while len(stim_images) < ntrials:
    np.random.shuffle(stim_list)
    for stim_fn in stim_list:
        stim_names.append(stim_fn)
        im = visual.ImageStim(win,stim_fn)
        im.size = im.size*.5
        stim_images.append(im)


tnum = 1 # Trial number

stim_images[0].draw()

while c.getTime() < iwt:
    pass


stim_images = stim_images[0:(ntrials)]

for i in range(len(stim_images)):
    log("{0:.3f}\t{1}\n".format(np.round(c.getTime(),decimals=3), 
        stim_names[i]))
    resp = []
    event.clearEvents()
    win.flip()
    fixation.draw()

    while (c.getTime() - iwt) < (soa*tnum - (soa-spd)):
        resp = event.getKeys(keyList=['q','p'],timeStamped=c)
        if len(resp) > 0:
            print(resp)
            log("{0:.3f}\t{1}\n".format(np.round(resp[0][1],decimals=3),resp[0][0]))
            break

    while (c.getTime() - iwt) < (soa*tnum - (soa-spd)):
        pass
    
    log("{0:.3f}\t{1}\toff\n".format(np.round(c.getTime(),decimals=3), stim_names[i]))    
    win.flip()

    if i < ntrials-1:
        stim_images[i+1].draw()
    
    
    if len(resp) == 0:
        while (c.getTime() - iwt) < soa*tnum:
            resp = event.getKeys(keyList=['q','p'],timeStamped=c)
            if len(resp) > 0:
                print(resp)
                log("{0:.3f}\t{1}\n".format(np.round(resp[0][1],decimals=3),resp[0][0]))
                
                break

    resp = event.getKeys(timeStamped=True)
    log(str(resp))

    while (c.getTime() - iwt) < soa*tnum:
        pass
    tnum += 1

log("END EXPERIMENT")

"""
open(logfn,"a").write("{0:.3f}\t{1}\n".format(np.round(c.getTime(), decimals=3),
    stim_list[tnum-1]))
resp = []
event.clearEvents()
win.flip()
fixation.draw()
while (c.getTime() - iwt) < (soa*tnum - (soa-spd)):
    resp = event.getKeys(keyList=['q','p'],timeStamped=c)
    if len(resp) > 0:
        print(resp)
        open(logfn,"a").write("{0:.3f}\t{1}\n".format(np.round(resp[0][1], decimals=3),resp[0][0]))
        break
while (c.getTime() - iwt) < (soa*tnum - (soa-spd)):
    pass

print(len(stim_list))
print(tnum-1)
open(logfn,"a").write("{0:.3f}\t{1} off\n".format(np.round(c.getTime(), decimals=3), stim_list[tnum-1]))
win.flip()


if len(resp) == 0:
    while (c.getTime() - iwt) < soa*tnum:
        resp = event.getKeys(keyList=['q','p'],timeStamped=c)
        if len(resp) > 0:
            print(resp)
            open(logfn,"a").write("{0:.3f}\t{1}\n".format(np.round(resp[0][1],
                decimals=3),resp[0][0]))
            break


    while (c.getTime() - iwt) < soa*tnum:
        pass
"""
##### print QR stamp for end of video
dbic.endRun(win)
