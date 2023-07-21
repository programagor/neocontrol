from .common import *

def dim2500k(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    color = black_body_rgb(2500,0.1)
    color = float_to_int(color)
    # Create an array of 240 copies of the colour and rest are zeros
    color_array = [color]*240 + [0]*(strip.numPixels()-240)
    interpolate_strip(strip,exit_event,color_array,10.0)
    #if not exit_event.is_set():
    #    fill(strip,color)