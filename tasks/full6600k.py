from .common import *

def full6600k(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    color = (255,255,255)
    fill(strip,color)