from .common import *

def blank(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    color = (0,0,0)
    interpolate_strip(strip,exit_event,[color]*strip.numPixels(),10.0)
    fill(strip,color)