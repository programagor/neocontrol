from .common import *

def rainbow(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    n = 1
    while not exit_event.is_set():
        n+=1

        
        for i in range(strip.numPixels()):
            color = hsv_to_rgb(n*0.002+i*0.002,1,1)
            color_obj = ws.Color(*color)
            strip.setPixelColor(i,color_obj)
        strip.show()
        exit_event.wait(0.1)
    exit_event.wait()