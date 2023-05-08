from .common import *

def sunrise(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):

    duration = 30.0 * 60
    temp_start = 50.0
    temp_end = 6000.0

    start_time = time.time()
    elapsed_time = 0.0

    while elapsed_time < duration and not exit_event.is_set():
        elapsed_time = time.time() - start_time
        time_frac = elapsed_time / duration
        current_temp = temp_start + time_frac**1.5 * (temp_end - temp_start)
        color = black_body_rgb(current_temp,time_frac**1.0)
        color_obj = ws.Color(*color)
        for i in range(strip.numPixels()):
            strip.setPixelColor(i,color_obj)
        strip.show()
        exit_event.wait(0.1)
    exit_event.wait(30*60)
    color = (0,0,0)
    fill(strip,color)