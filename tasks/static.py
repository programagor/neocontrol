from .common import *

def static(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    if arg is not None:
        color = arg
        color_obj = ws.Color(*color)
        for i in range(strip.numPixels()):
            strip.setPixelColor(i,color_obj)
        strip.show()
    exit_event.wait()