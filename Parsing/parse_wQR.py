from pyzbar.pyzbar import decode, ZBarSymbol
import moviepy.editor as ed
import sys
import numpy as np
import time

starttime = time.time()

vid = ed.VideoFileClip(sys.argv[1])


clips = []
qrData = {}

inRun = False

clip_start = None
acqNum = None
runNum = None


#for f in vid.iter_frames(with_times=True):

for t in np.arange(0,vid.duration,.05):

    f = vid.get_frame(t)

    if np.mod(t,10) == 0:
        print(t)
    
    cod = decode(f, symbols=[ZBarSymbol.QRCODE])
    if len(cod)>0:
        data = eval(eval(str(cod[0].data)).decode('utf-8'))

        if ('runStart' in data) and (not inRun):
            print("found start: {}".format(t))
            acqNum = data['acqNum']
            runNum = data['runNum']

            vv = vid.subclip(t-.1, t+.1)
            for ff in vv.iter_frames(with_times=True):
                cod = decode(ff[1], symbols=[ZBarSymbol.QRCODE])
                if len(cod)>0:
                    clip_start = t-.1+ff[0]
                    inRun = True
                    break
            print("found start: {}".format(clip_start))
        if ('runEnd' in data) and inRun:
            print("found run end: {}".format(t))
            vv = vid.subclip(t-.1, t+.1)
            for ff in vv.iter_frames(with_times=True):
                cod = decode(ff[1], symbols=[ZBarSymbol.QRCODE])
                if len(cod)>0:
                    clips.append({'clip_times':(clip_start,t-.1+ff[0]),
                                    'acqNum':acqNum, 'runNum':runNum})
                    inRun = False
                    clip_start = acqNum = runNum =None
                    break
 


print(clips)
print(time.time() - starttime)

