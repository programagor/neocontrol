from .common import *

def purple(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):
    t_rate = 0.275
    i_rate = 0.055
    start_time = time.time()
    elapsed_time = 0
    while not exit_event.is_set():
        for i in range(strip.numPixels()):
            # Strip has U topology, so loop back in the middle
            if i < strip.numPixels() / 2:
                pos = i
            else:
                pos = strip.numPixels() - i
            # hue progresses along the strip (i) and with time (elapsed_time)
            # saturation and value are always 1 (full)
            pos = elapsed_time*t_rate+pos*i_rate
            hue_mean = 0.89
            hue_var = 0.12
            hue = hue_mean + hue_var * math.sin(pos)
            color = hsv_to_rgb(hue,1,1)
            color_obj = ws.Color(*color)
            strip.setPixelColor(i,color_obj)
        strip.show()
        exit_event.wait(0.1)
        elapsed_time = time.time() - start_time
