from .common import *

def sunset(strip: ws.PixelStrip, exit_event: threading.Event, arg = None):

    duration = 2.0 * 60
    temp_start = 500.0
    temp_end = 3500.0

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
        current_temp = temp_start + (1-time_frac)**temp_curve * (temp_end - temp_start)
        # Calculate the colour from the temperature (plus brightness from time)
        color = black_body_rgb(current_temp,(1-time_frac)**bright_curve)
        # Add the random noise to the colour:
        # First tile the colour array to match the number of pixels
        # Then add the noise
        # Clamping to 0-255 is done later in the float_to_int function
        colors = np.tile(np.array(color),(strip.numPixels(),1)) + jitter

        # Set the colour of each pixel
        for i in range(strip.numPixels()):
            # Convert the np.array of floats to a tuple of ints
            color =  float_to_int(colors[i])
            # because the ws.Color constructor expects that
            color_obj = ws.Color(*color)
            # Set the pixel colour
            strip.setPixelColor(i,color_obj)
        # When all the pixels are set, send the data to the LEDs
        strip.show()
        # Wait a bit before looping again
        exit_event.wait(0.1)
        # The loop takes time anyway, but we don't want to starve the HTTP server
        # Update the elapsed time and loop again
        elapsed_time = time.time() - start_time
    # At the end of the sunset sequence, turn off the LEDs.
    if not exit_event.is_set():
        color = (0,0,0)
        fill(strip,color)