from .common import *

def blank(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    color = (0,0,0)
    color_obj = ws.Color(*color)
    for i in range(strip.numPixels()):
        strip.setPixelColor(i,color_obj)
    strip.show()
    exit_event.wait()