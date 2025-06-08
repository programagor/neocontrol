from .common import *
import random
import numpy as np
import time
import threading

class Firefly:
    def __init__(self, strip_length):
        self.strip_length = strip_length
        self.position = random.uniform(0, strip_length)
        
        # Assign hue using Gaussian distribution, then take modulo 1
        self.hue = random.gauss(0, 0.02) % 1
        
        self.duration = max(2, random.gauss(5, 3))  # Ensure duration is positive
        self.speed = random.gauss(0, 1)
        self.start_time = time.time()
        self.alive = True

    def update(self, current_time):
        elapsed_time = current_time - self.start_time
        if elapsed_time > self.duration:
            self.alive = False
            return
        self.position = (self.position + self.speed * 0.1) % self.strip_length  # Update position and wrap around

    def get_brightness(self, current_time):
        elapsed_time = current_time - self.start_time
        half_duration = self.duration / 2
        if elapsed_time < half_duration:
            # Ramp up
            return elapsed_time / half_duration
        else:
            # Ramp down
            return 1 - (elapsed_time - half_duration) / half_duration

def blend_colors(color1, color2):
    return (
        int(max(0, min(255, color1[0] + color2[0]))),
        int(max(0, min(255, color1[1] + color2[1]))),
        int(max(0, min(255, color1[2] + color2[2])))
    )

def fairy_lights_red(strip: ws.PixelStrip, exit_event: threading.Event, arg=None):
    strip_length = strip.numPixels()
    fireflies = []
    while not exit_event.is_set():
        current_time = time.time()

        # Add new fireflies based on Poisson distribution
        if random.expovariate(1 / 3) < 2.5:  # Adjust rate as needed
            fireflies.append(Firefly(strip_length))

        # Initialize strip with black color
        pixel_colors = [(0, 0, 0)] * strip_length

        # for firefly in fireflies:
        #    firefly.update(current_time)
        #    if not firefly.alive:
        #        fireflies.remove(firefly)
        # this causes issues, let's try differently
        to_remove = []
        for i in range(len(fireflies)):
            firefly = fireflies[i]
            firefly.update(current_time)
            if not firefly.alive:
                to_remove.append(i)
        for i in reversed(to_remove):
            fireflies.pop(i)

        # Update and draw fireflies
        for firefly in fireflies:
            pos = firefly.position
            int_pos = int(pos)
            next_pos = (int_pos + 1) % strip_length
            frac = pos - int_pos
            color = hsv_to_rgb(firefly.hue, 1, 1)
            brightness = firefly.get_brightness(current_time)
            # Ensure blended colors are tuples of RGB values
            blended_color1 = blend_colors(pixel_colors[int_pos], (
                int(color[0] * brightness * (1 - frac)), int(color[1] * brightness * (1 - frac)),
                int(color[2] * brightness * (1 - frac))))
            blended_color2 = blend_colors(pixel_colors[next_pos], (
                int(color[0] * brightness * frac), int(color[1] * brightness * frac),
                int(color[2] * brightness * frac)))
            pixel_colors[int_pos] = blended_color1
            pixel_colors[next_pos] = blended_color2

        # Set colors on the strip
        for i in range(strip_length):
            strip.setPixelColor(i, ws.Color(*pixel_colors[i]))

        strip.show()
        exit_event.wait(0.001)
