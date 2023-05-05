from .common import *

def blank(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    color = (0,0,0)
    fill(strip,color)