from .common import *

def full6600k(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):

    color = (255,255,255)
    interpolate_strip(strip,exit_event,[color]*strip.numPixels(),10.0,1)
    if not exit_event.is_set():
        fill(strip,color)