from .common import *

def full2500k(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    color = black_body_rgb(2500)
    color = float_to_int(color)
    fill(strip,color)