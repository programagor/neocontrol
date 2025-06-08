from .common import *

def rainbow(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    t_rate = 0.015
    i_rate = 0.002
    start_time = time.time()
    elapsed_time = 0
    while not exit_event.is_set():
        for i in range(strip.numPixels()):
            # Strip has zigzag topology, so loop back every 120 pixels
            #j = i % 240
            #if j < 120:
            #    pos = j
            #else:
            #    pos = 240 - j
            pos = i
            # hue progresses along the strip (i) and with time (elapsed_time)
            # saturation and value are always 1 (full)
            color = hsv_to_rgb(elapsed_time*t_rate+pos*i_rate,1,1)
            color_obj = ws.Color(*color)
            strip.setPixelColor(i,color_obj)
        strip.show()
        exit_event.wait(0.1)
        elapsed_time = time.time() - start_time
