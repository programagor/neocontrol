from .common import ws, threading, black_body_rgb, float_to_int, interpolate_strip, fill

def dim1500k(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    color = black_body_rgb(1500,0.1)
    color = float_to_int(color)
    # Create an array of 240 copies of the colour and rest are zeros
    color_array = [color]*240 + [(0,0,0)]*(strip.numPixels()-240)
    interpolate_strip(strip,exit_event,color_array,10.0)
    if not exit_event.is_set():
    # fill the strip with color_array
    for i in range(strip.numPixels()):
        strip.setPixelColor(i,color_array[i])