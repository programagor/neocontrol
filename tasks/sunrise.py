from .common import *

def sunrise(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):

    duration = 30.0 * 60
    temp_start = 500.0
    temp_end = 6600.0

    temp_curve = 1.5
    bright_curve = 1.0

    start_time = time.time()
    elapsed_time = 0.0

    # Prepare random noise for each pixel and colour channel
    # This is to break up banding in the gradient (all LEDs changing at once)
    jitter = np.random.randint(0,255,(strip.numPixels(),3))

    # Loop until the exit event is set or the duration is reached
    while elapsed_time < duration and not exit_event.is_set():
        # How far through the duration are we?
        time_frac = elapsed_time / duration
        # Calculate the current temperature
        current_temp = temp_start + time_frac**temp_curve * (temp_end - temp_start)
        # Calculate the colour from the temperature (plus brightness from time)
        color = black_body_rgb(current_temp,time_frac**bright_curve)
        # use fixed point arithmetic
        # instead of dealing with floats, which are slow, we use integers scaled up by 256
        color = tuple(map(lambda x: int(x*256),color))
        # Add the random noise to the colour
        colors = np.clip(np.tile(color,(strip.numPixels(),1)) + jitter , 0, 65535)
        # shift each number to the right by 8 bits (divide by 256)
        colors >>= 8

        # Set the colour of each pixel
        for i in range(strip.numPixels()):
            # Convert the np.array of floats to a tuple of ints
            color = float_to_int(colors[i])
            # because the ws.Color constructor expects that
            color_obj = ws.Color(*color)
            # Set the pixel colour
            strip.setPixelColor(i,color_obj)
        # When all the pixels are set, send the data to the LEDs
        strip.show()
        # Wait a bit before looping again
        exit_event.wait(0.01)
        # The loop takes time anyway, but we don't want to starve the HTTP server
        # Update the elapsed time and loop again
        elapsed_time = time.time() - start_time
    # After the sunrise sequence is finished, wait 30 minutes and then turn off the LEDs
    exit_event.wait(30*60)
    # Only turn off the LEDs if the exit event hasn't been set
    if exit_event.is_set():
        return
    color = (0,0,0)
    interpolate_strip(strip,exit_event,[color]*strip.numPixels(),10.0)
    if exit_event.is_set():
        return
    fill(strip,color)