import time
import board
import neopixel

# Configure the data pin and total number of LEDs
PIXEL_PIN = board.GP2
# PIXEL_PIN = board.GP16

NUM_PIXELS = 8  # Adjust this to match the number of LEDs on your strip
# NUM_PIXELS = 1  # Adjust this to match the number of LEDs on your strip

# Initialize the NeoPixel strip
# auto_write=False allows you to change multiple pixels before pushing the update
pixels = neopixel.NeoPixel(
    PIXEL_PIN, 
    NUM_PIXELS, 
    brightness=0.3, 
    auto_write=False
)

def color_chase(color, wait):
    """Lights up one pixel at a time sequentially along the strip."""
    for i in range(NUM_PIXELS):
        pixels[i] = color
        pixels.show()
        time.sleep(wait)

def wheel(pos):
    """Generates rainbow colors across 0-255 positions."""
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)

def rainbow_cycle(wait):
    """Smoothly cycles a rainbow across the entire strip."""
    for j in range(256):
        for i in range(NUM_PIXELS):
            pixel_index = (i * 256 // NUM_PIXELS) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)

# Primary color definitions (Red, Green, Blue)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CLEAR = (0, 0, 0)

print("Starting NeoPixel loop on GP2...")

while True:
    # 1. Run solid color fills
    color_chase(RED, 0.05)
    color_chase(GREEN, 0.05)
    color_chase(BLUE, 0.05)
    
    # 2. Run a rainbow animation loop
    print("Running rainbow cycle...")
    for _ in range(3):  # Repeat rainbow 3 times
        rainbow_cycle(0.01)
        
    # Clear the strip before repeating
    pixels.fill(CLEAR)
    pixels.show()
    time.sleep(1)

