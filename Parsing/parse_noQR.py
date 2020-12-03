import moviepy.editor as ed
import sys
import numpy as np
import time
import pytesseract as tess
import matplotlib.pyplot as plt
import time

vid = ed.VideoFileClip(sys.argv[1])

#frame_t = sys.argv[2]

#[(40, 114), (125, 130)]


sig_box=(490,590,470,810)

end_sig_box = (114,130,40,125)

sig="Waiting for scan"
end_sig = "PsychoP"

def find_starts(vid, t_interval=None, step=None, 
        sig=None, sig_box=None, start_found=False, sig_appear=False):

    x,y,p,q = sig_box

    t1 = t_interval[0]


    starts = []


    for t in np.arange(t_interval[0], t_interval[1], step):


        f = tess.image_to_string(vid.get_frame(t)[x:y,p:q,:])


        if sig in f:
            t1 = t
            start_found = True

        else:
            if start_found:
                print("start found at: {} to {}-- {}".format(t1,t,f))
                starts.append((t1,t))
                start_found = False



    if len(starts) == 0:
        starts = [(t1,t_interval[1])]

    return starts

def find_appearing_sig(vid, t_interval, step, sig, sig_box):
    x,y,p,q = sig_box

    t1 = t_interval[0]
    t = t_interval[1]
    for t in np.arange(t_interval[0], t_interval[1], step):
        f = tess.image_to_string(vid.get_frame(t)[x:y,p:q,:])
        
        if sig not in f:
            t1 = t
        else:
            return (t1, t)
    print("Warning: did not find appearing signal {} in {}".format(sig,str(t_interval)))
    return (t1, t)

def refine_starts(vid, starts, step=1):
# initial t_interval is (0, vid.duration)
    ref_starts = []
    for start in starts:
        rs = find_starts(vid, t_interval=(start[0],start[1]+step), step=step, 
                sig=sig, sig_box=sig_box, start_found=True)
        ref_starts = ref_starts + rs

    return ref_starts

"""
starts = find_starts(vid, t_interval=(2500,vid.duration),step=5,
                    sig=sig, sig_box=sig_box)


print("First pass: starts ==> {}".format(starts))

ref_starts = refine_starts(vid, starts,step=1)
ref_starts = refine_starts(vid, ref_starts, step=.02)
"""
ref_starts = [(2957.2, 2957.22), (3386.8199999999993, 3386.8399999999992),
        (3823.7399999999993, 3823.7599999999993), (4254.360000000008,
            4254.380000000008), (4669.080000000002, 4669.100000000002),
        (5124.660000000014, 5124.680000000015), (5180.040000000001,
            5180.060000000001), (5672.680000000015, 5672.700000000015),
        (6178.220000000005, 6178.240000000005), (6670.080000000002,
            6670.100000000002)]

#print("Second pass: refined starts ==> {}".format(ref_starts))

starts = [(ref_starts[x][0],ref_starts[x+1][0]) for x in
        range(0,len(ref_starts)-1)]
starts.append((ref_starts[-1][0],vid.duration))

#print(starts)

#intv = (5124.660000000014, 5180.040000000001)
#endsig_interval = find_appearing_sig(vid,intv,
#        step=5,sig=end_sig,sig_box=end_sig_box)
#print(endsig_interval)



ends = []

for intv in starts:
    endsig_interval = find_appearing_sig(vid,intv,
        step=5,sig=end_sig,sig_box=end_sig_box)
    ends.append(endsig_interval)
    print(endsig_interval)

ends = [find_appearing_sig(vid,intv,
        step=1,sig=end_sig,sig_box=end_sig_box) for intv in ends]

ends = [find_appearing_sig(vid,intv,
        step=.02,sig=end_sig,sig_box=end_sig_box) for intv in ends]

print(ends)

