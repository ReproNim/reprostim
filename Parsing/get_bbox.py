from psychopy import visual, event
from PIL import Image

image_fn = "test.jpg"

im = Image.open(image_fn)

h = im.height
w = im.width

win = visual.Window()

im = visual.ImageStim(win,image_fn)
im.draw()
win.flip()



