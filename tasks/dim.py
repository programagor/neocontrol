from .common import *

def dim(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    color = (8,3,1)
    fill(strip,color)
    exit_event.wait()