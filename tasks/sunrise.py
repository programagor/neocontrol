from .common import *

def sunrise(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):

    duration = 30.0 * 60
    temp_start = 50.0
    temp_end = 6000.0

    start_time = time.time()
    elapsed_time = 0.0

    jitter = np.random.rand(strip.numPixels(),3) - 0.5

    while elapsed_time < duration and not exit_event.is_set():
        time_frac = elapsed_time / duration
        current_temp = temp_start + time_frac**1.5 * (temp_end - temp_start)
        color = black_body_rgb(current_temp,time_frac**1.0)
        color = np.tile(np.array(color),(strip.numPixels(),1)) + jitter
        color = np.clip(color,0.0,255.0)
        color = np.array(color,dtype=np.uint8)
        for i in range(strip.numPixels()):
            color_obj = ws.Color(*color[i])
            strip.setPixelColor(i,color_obj)
        strip.show()
        exit_event.wait(0.1)
        elapsed_time = time.time() - start_time
    exit_event.wait(30*60)
    color = (0,0,0)
    fill(strip,color)