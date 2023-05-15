from .common import *

def full3500k(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    color = black_body_rgb(3500)
    color = float_to_int(color)
    fill(strip,color)