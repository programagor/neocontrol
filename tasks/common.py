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

def rgb_black_body(rgb=(255,255,255)):
    """Function to estimate black body temperature from RGB"""
    # TODO
    return 6600

def float_to_int(color):
    """Function to convert float RGB to int RGB and clamp values to 0-255"""
    return tuple(map(lambda x: max(0,min(255,int(x))),color))


def hsv_to_rgb(hue, sat, val):
    """Function to calculate RGB from HSV
    Range: h: 0-1, s: 0-1, v: 0-1"""
    result = (0,0,0)
    if sat == 0.0:
        return result
    c_1 = int(hue*6.0)
    c_2 = (hue*6.0) - c_1
    p_1,p_2,p_3 = int(255*(val*(1.0 - sat))), int(255*(val*(1.0 - sat*c_2))), int(255*(val*(1.0 - sat*(1.0 - c_2))))
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
