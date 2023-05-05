from .common import *

def static(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    fill(strip,arg)