#!/usr/bin/env python

import json
from pyzbar.pyzbar import decode, ZBarSymbol
import cv2
import sys
import numpy as np
import time

starttime = time.time()
cap = cv2.VideoCapture(sys.argv[1])

# Check if the video opened successfully
if not cap.isOpened():
    print("Error: Could not open video.", file=sys.stderr)
    sys.exit(1)

clips = []
qrData = {}

inRun = False

clip_start = None
acqNum = None
runNum = None


#for f in vid.iter_frames(with_times=True):

# TODO: just use tqdm for progress indication
iframe = 0
record = None

def finalize_record():
    global record
    record['frame_end'] = iframe
    record['time_end'] = 'TODO'
    print(json.dumps(record))
    record = None

while True:
    iframe += 1
    ret, frame = cap.read()
    if not ret:
        break
    
    f = np.mean(frame, axis=2)  # poor man greyscale from RGB

    if np.mod(iframe,50) == 0:
        print(f"iframe={iframe} {np.std(f)}", file=sys.stderr)
    
#    if np.std(f) > 10:
#        cv2.imwrite('grayscale_image.png', f)
#        import pdb; pdb.set_trace()

    cod = decode(f, symbols=[ZBarSymbol.QRCODE])
    if len(cod) > 0:
        assert len(cod) == 1, f"Expecting only one, got {len(cod)}"
        data = eval(eval(str(cod[0].data)).decode('utf-8'))
        if record is not None:
            if data == record['data']:
                # we are still in the same QR code record
                continue
            # It is a different QR code! we need to finalize current one
            finalize_record()
        # We just got beginning of the QR code!
        record = {
            'frame_start': iframe,
            'time_start': "TODO-figureout",
            'data' : data
        }
    else:
        if record:
            finalize_record()
 
if record:
    finalize_record()
