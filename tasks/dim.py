from .common import *

def dim(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    color = (20,6,5)
    interpolate_strip(strip,exit_event,[color]*strip.numPixels(),10.0)
    fill(strip,color)