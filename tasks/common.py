"""Common functions for all tasks"""
import datetime
import math         # pylint: disable=unused-import
import random       # pylint: disable=unused-import
import threading    # pylint: disable=unused-import
import time         # pylint: disable=unused-import
import numpy as np  # pylint: disable=unused-import

now = datetime.datetime.now

# Check if rpi_ws281x library is available
try:
    import rpi_ws281x as ws # type: ignore
except ImportError:
    # Define dummy class for local testing
    class DummyPixelStrip:
        """Dummy rpi_ws281x-like class for local testing"""
        def __init__(self, *args, **kwargs): # pylint: disable=unused-argument
            self.num_pixels = kwargs.get('led_count', 4)

        def begin(self):
            """Dummy begin method"""
            print(f"[{now()}] Dummy strip: begin")

        def setPixelColor(self, i, color_obj): # pylint: disable=invalid-name
            """Dummy setPixelColor method"""
            print(f"[{now()}] Dummy strip: set pixel[{i}] to {color_obj}")

        def show(self):
            """Dummy show method"""
            print(f"[{now()}] Dummy strip: show")

        def numPixels(self): # pylint: disable=invalid-name
            """Dummy numPixels method"""
            return self.num_pixels

    def DummyColor(*color): # pylint: disable=invalid-name
        """Dummy Color method"""
        return color

    # Replace rpi_ws281x with dummy implementation
    ws = type("Dummy_rpi_ws281x", (object,), { # pylint: disable=invalid-name
        "PixelStrip": DummyPixelStrip,
        "Color": DummyColor,
        "WS2811_STRIP_GRB": "Dummy_WS2811_STRIP_GRB"
    })

def black_body_rgb(temp,brightness=1.0):
    """Function to calculate RGB from black body temperature
    Source: https://tannerhelland.com/2012/09/18/convert-temperature-rgb-algorithm-code.html"""
    temp = temp / 100.0
    brightness = max(0,min(1,brightness))
    red, grn, blu = 0, 0, 0
    if temp <= 66:
        red = 255
        grn = temp
        grn = 99.4708025861 * math.log(grn) - 161.1195681661
    else:
        red = temp - 60
        red = 329.698727446 * (red ** -0.1332047592)
        grn = temp - 60
        grn = 288.1221695283 * (grn ** -0.0755148492)
    if temp >= 66:
        blu = 255
    elif temp <= 19:
        blu = 0
    else:
        blu = temp - 10
        blu = 138.5177312231 * math.log(blu) - 305.0447927307
    return red*brightness, grn*brightness, blu*brightness

def generate_temp_lut(min_temp=500, max_temp=25000, step=0.02):
    """Function to generate a lookup table for black body temperature estimation"""
    lut = {}

    temp = min_temp
    while temp <= max_temp:
        rgb = black_body_rgb(temp)
        #lut[rgb] = temp
        #only keep 2 decimal places
        lut[rgb] = int(round(temp, 0))
        temp *= 1+step

    return lut

temp_lut = generate_temp_lut()


def rgb_black_body(target_rgb=(255,255,255)):
    """Function to estimate black body temperature from RGB"""
    closest_rgb = min(temp_lut.keys(), key=lambda rgb: (rgb[0] - target_rgb[0]) ** 2 + (rgb[1] - target_rgb[1]) ** 2 + (rgb[2] - target_rgb[2]) ** 2)
    return temp_lut[closest_rgb]

def float_to_int(color):
    """Function to convert float RGB to int RGB and clamp values to 0-255"""
    return tuple(map(lambda x: max(0,min(255,int(x))),color))

def packed24_to_rgb(packed):
    """Function to convert packed 24-bit RGB to tuple of ints"""
    return (packed >> 16) & 0xFF, (packed >> 8) & 0xFF, packed & 0xFF

def strip_to_rgb(strip: ws.PixelStrip):
    """Function to convert strip to list of RGB tuples"""
    color_data = strip.getPixels()
    return [packed24_to_rgb(color_data[i]) for i in range(strip.numPixels())]

def strip_to_temp(strip: ws.PixelStrip):
    """Function to convert strip to average black body temperature"""
    rgb_data = strip_to_rgb(strip)
    # Find the average colour of the strip
    avg_color = np.mean(rgb_data,axis=0)
    # scale it so that the largest component is 255
    if(max(avg_color) > 0):
        avg_color *= 255.0/max(avg_color)
    # convert to tuple of ints
    avg_color = tuple(map(int,avg_color))
    # estimate the temperature from the average colour
    avg_color = rgb_black_body(avg_color)
    return avg_color

def interpolate_strip(strip: ws.PixelStrip, exit_event:threading.Event, final_colors: list[tuple[int,int,int]], duration: float, curve: float = 0.5):
    """Function to interpolate between initial strip state and final strip state"""
    jitter = np.random.randint(0,255,(strip.numPixels(),3))
    rgb_data = strip_to_rgb(strip)
    rgb_data = np.array(rgb_data)*256
    final_colors = np.array(final_colors)*256
    diff = final_colors-rgb_data
    start_time = time.time()
    elapsed_time = 0
    print(f"[{datetime.datetime.now()}] Interpolate strip over {duration} seconds")
    while elapsed_time < duration and not exit_event.is_set():
        frac = int(((elapsed_time / duration)**curve)*16536)
        current = rgb_data+(frac*diff)//16536 + jitter
        current = current.astype(int)
        current >>= 8
        for i in range(strip.numPixels()):
            color = float_to_int(current[i])
            color_obj = ws.Color(*color)
            strip.setPixelColor(i,color_obj)
        strip.show()
        exit_event.wait(0.01)
        elapsed_time = time.time() - start_time
    print(f"[{datetime.datetime.now()}] Interpolation finished")

def hsv_to_rgb(hue, sat, val):
    """Function to calculate RGB from HSV
    Range: h: 0-1, s: 0-1, v: 0-1"""
    result = (0,0,0)
    if sat == 0.0:
        return result
    c_1 = int(hue*6.0)
    c_2 = (hue*6.0) - c_1
    p_1 = int(255*(val*(1.0 - sat)))
    p_2 = int(255*(val*(1.0 - sat*c_2)))
    p_3 = int(255*(val*(1.0 - sat*(1.0 - c_2))))
    val = int(255*val)
    switcher = {
        0: (val, p_3, p_1),
        1: (p_2, val, p_1),
        2: (p_1, val, p_3),
        3: (p_1, p_2, val),
        4: (p_3, p_1, val),
        5: (val, p_1, p_2)
    }
    return switcher.get(c_1 % 6, (0,0,0))

def fill(strip: ws.PixelStrip, color = None):
    """Function to fill the whole strip with a single colour"""
    if color is not None:
        print(f"[{datetime.datetime.now()}] Fill with color {color}")
        color_obj = ws.Color(*color)
        for i in range(strip.numPixels()):
            strip.setPixelColor(i,color_obj)
        strip.show()
