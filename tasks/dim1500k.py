from .common import ws, threading, black_body_rgb, float_to_int, interpolate_strip, fill

def dim1500k(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    color = black_body_rgb(1500,0.1)
    color = float_to_int(color)
    interpolate_strip(strip,exit_event,[color]*240,10.0)
    if not exit_event.is_set():
        fill(strip,color)
