from .common import *

def sunrise(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):

    duration = 30.0 * 60
    temp_start = 50.0
    temp_end = 6000.0

    temp_curve = 1.5
    bright_curve = 1.0

    start_time = time.time()
    elapsed_time = 0.0

    # Prepare random noise for each pixel and colour channel
    # This is to break up banding in the gradient (all LEDs changing at once)
    jitter = np.random.rand(strip.numPixels(),3) - 0.5

    # Loop until the exit event is set or the duration is reached
    while elapsed_time < duration and not exit_event.is_set():
        # How far through the duration are we?
        time_frac = elapsed_time / duration
        # Calculate the current temperature
        current_temp = temp_start + time_frac**temp_curve * (temp_end - temp_start)
        # Calculate the colour from the temperature (plus brightness from time)
        color = black_body_rgb(current_temp,time_frac**bright_curve)
        # Add the random noise to the colour
        # First tile the colour array to match the number of pixels
        # Then add the noise
        # Then clip to 0-255
        color = np.clip(np.tile(np.array(color),(strip.numPixels(),1)) + jitter,0.0,255.0)

        # Set the colour of each pixel
        for i in range(strip.numPixels()):
            # Convert the np.array of floats to a tuple of ints
            color_tuple = tuple(map(int,tuple(color[i])))
            # because the ws.Color constructor expects that
            color_obj = ws.Color(*color_tuple)
            # Set the pixel colour
            strip.setPixelColor(i,color_obj)
        # When all the pixels are set, send the data to the LEDs
        strip.show()
        # Wait a bit before looping again
        #exit_event.wait(0.1)
        # ...or not, because the loop takes a while anyway
        # Update the elapsed time and loop again
        elapsed_time = time.time() - start_time
    # After the sunrise sequence is finished, wait 30 minutes and then turn off the LEDs
    exit_event.wait(30*60)
    # Only turn off the LEDs if the exit event hasn't been set
    if not exit_event.is_set():
        color = (0,0,0)
        fill(strip,color)