import array
import time
from machine import Pin
import rp2

MAX_LUM =100

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
	T1 = 2
	T2 = 5
	T3 = 3
	wrap_target()
	label("bitloop")
	out(x, 1) .side(0) [T3 - 1]
	jmp(not_x, "do_zero") .side(1) [T1 - 1]
	jmp("bitloop") .side(1) [T2 - 1]
	label("do_zero")
	nop() .side(0) [T2 - 1]
	wrap()


# Create the StateMachine, outputting on Pin(12) — this can vary between devices.
SM = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(16))

def cycle(
	max_lum=MAX_LUM,
	):
	# Start the StateMachine, it will wait for data on its FIFO.
	SM.active(1)

	# Color change
	g = 0
	ix = 0
	while True:
		for i in range(0,max_lum):
			r=i
			b=max_lum-i
			rgb =(g<<24) | (r<<16) | (b<<8)
			_rgb = array.array("I", [rgb])
			SM.put(_rgb)
			time.sleep_ms(10)
		time.sleep_ms(300)
		for i in range(0,max_lum):
			g=i
			r=max_lum-i
			rgb =(g<<24) | (r<<16) | (b<<8)
			_rgb = array.array("I", [rgb])
			SM.put(_rgb)
			time.sleep_ms(10)
		time.sleep_ms(300)
		for i in range(0,max_lum):
			b=i
			g=max_lum-i
			rgb =(g<<24) | (r<<16) | (b<<8)
			_rgb = array.array("I", [rgb])
			SM.put(_rgb)
			time.sleep_ms(10)
		time.sleep_ms(300)
		ix+=1
		if ix >= 2:
			print(f"I have cycled {ix} times now.")

def set(
	red=128,
	green=0,
	blue=128,
	):
	"""
	Set the onboard LED to the respective RBG colour, with values ranging from 0 to 255.
	"""

	# Start the StateMachine, it will wait for data on its FIFO.
	SM.active(1)

	rgb =(red<<16) | (green<<24) | (blue<<8)
	_rgb = array.array("I", [rgb])
	SM.put(_rgb)
