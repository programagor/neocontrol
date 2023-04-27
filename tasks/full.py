from .common import *

def full(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    color = (255,255,255)
    color_obj = ws.Color(*color)
    for i in range(strip.numPixels()):
        strip.setPixelColor(i,color_obj)
    strip.show()
    exit_event.wait()