from .common import *

def static(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    if arg is not None:
        color = arg
        fill(strip,color)