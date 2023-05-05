from .common import *

def dim(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    color = (20,6,5)
    fill(strip,color)