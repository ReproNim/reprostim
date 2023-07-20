from mpremote import pyboard
from time import time


port = "/dev/ttyACM0"
pyb = pyboard.Pyboard(port, 115200)

while True:
    pyb.enter_raw_repl()
    t0 = time()
    pyb.exec_raw_no_follow('import board_side; board_side.return_message()')
    t1 = time()
    print(str((t1 - t0) * 1000) + " ms")
