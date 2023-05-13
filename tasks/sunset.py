from .common import *

def sunset(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):

    duration = 2.0 * 60
    temp_start = 100.0
    temp_end = 4000.0

    start_time = time.time()
    elapsed_time = 0.0

    jitter = np.random.rand(strip.numPixels(),3) - 0.5

    while elapsed_time < duration and not exit_event.is_set():
        time_frac = elapsed_time / duration
        current_temp = temp_start + (1-time_frac)**1.5 * (temp_end - temp_start)
        color = black_body_rgb(current_temp,(1-time_frac)**1.0)
        color = np.clip(np.tile(np.array(color),(strip.numPixels(),1)) + jitter,0.0,255.0)

        for i in range(strip.numPixels()):
            color_tuple = tuple(map(int,tuple(color[i])))
            color_obj = ws.Color(*color_tuple)
            strip.setPixelColor(i,color_obj)
        strip.show()
        #exit_event.wait(0.1)
        elapsed_time = time.time() - start_time
    color = (0,0,0)
    fill(strip,color)