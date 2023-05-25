from .common import *

def full2500k(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    color = black_body_rgb(2500)
    color = float_to_int(color)
    interpolate_strip(strip,exit_event,[color]*strip.numPixels(),10.0,1)
    if not exit_event.is_set():
        fill(strip,color)