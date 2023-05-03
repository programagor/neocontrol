import importlib
import time
import numpy as np
import threading

# Check if rpi_ws281x library is available
rpi_ws281x_spec = importlib.util.find_spec("rpi_ws281x")
if rpi_ws281x_spec is not None:
    import rpi_ws281x as ws
else:
    # Define dummy class for local testing
    class DummyPixelStrip:
        def __init__(self, *args, **kwargs):
            self.num_pixels = kwargs.get('led_count', 4)

        def begin(self):
            print("Dummy strip: begin")

        def setPixelColor(self, i, color_obj):
            print(f"Dummy strip: set pixel color at index {i} to {color_obj}")

        def show(self):
            print("Dummy strip: show")

        def numPixels(self):
            return self.num_pixels

    def DummyColor(*color):
        return color

    # Replace rpi_ws281x with dummy implementation
    ws = type("Dummy_rpi_ws281x", (object,), {
        "PixelStrip": DummyPixelStrip,
        "Color": DummyColor,
        "WS2811_STRIP_GRB": "Dummy_WS2811_STRIP_GRB"
    })
    

def black_body_rgb(temp,brightness):
    temp = temp / 100.0
    brightness = max(0,min(1,brightness))
    r, g, b = 0, 0, 0


    if temp <= 66:
        r = 255
        g = temp
        g = 99.4708025861 * np.log(g) - 161.1195681661
    else:
        r = temp - 60
        r = 329.698727446 * (r ** -0.1332047592)
        g = temp - 60
        g = 288.1221695283 * (g ** -0.0755148492)

    if temp >= 66:
        b = 255
    elif temp <= 19:
        b = 0
    else:
        b = temp - 10
        b = 138.5177312231 * np.log(b) - 305.0447927307

    r = max(min(r, 255), 0)
    g = max(min(g, 255), 0)
    b = max(min(b, 255), 0)

    return int(r*brightness), int(g*brightness), int(b*brightness)

# Function to calculate RGB from HSV
def hsv_to_rgb(h, s, v):
    if s == 0.0: return (v, v, v)
    i = int(h*6.0)
    f = (h*6.0) - i
    p,q,t = int(255*(v*(1.0 - s))), int(255*(v*(1.0 - s*f))), int(255*(v*(1.0 - s*(1.0 - f))))
    v = int(255*v)
    i %= 6
    if i == 0: return (v, t, p)
    if i == 1: return (q, v, p)
    if i == 2: return (p, v, t)
    if i == 3: return (p, q, v)
    if i == 4: return (t, p, v)
    if i == 5: return (v, p, q)

def fill(strip: ws.PixelStrip, color = None):
    color_obj = ws.Color(*color)
    for i in range(strip.numPixels()):
        strip.setPixelColor(i,color_obj)
    strip.show()