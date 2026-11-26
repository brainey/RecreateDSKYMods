import time
import board
import keypad
import neopixel
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

print("Starting DSKY LED and Keypad Controller - Google Version 2")
# --- 1. LED Configuration ---
LED_PIN = board.GP2
NUM_LEDS = 28
pixels = neopixel.NeoPixel(LED_PIN, NUM_LEDS, brightness=0.5, auto_write=False)

# LED Interface Command Opcodes
CMD_SET_BRIGHTNESS = 0x01
CMD_SET_RANGE      = 0x02
CMD_SHOW           = 0x03

# the firmware should provide a mapping between logical indicators and physical LEDs
# I don't think the labels are need here ?
INDICATORS = {
    1: {"label": "UPLINK ACTY", "leds": (0,1), "pins": "D27/D28", "phys_leds": (16, 17)},
    2: {"label": "TEMP",        "leds": (2,3), "pins": "D1/D2",   "phys_leds": (18, 19)},
    3: {"label": "NO ATT",      "leds": (4,5), "pins": "D25/D26", "phys_leds": (14, 15)},
    4: {"label": "GIM LOCK",    "leds": (6,7), "pins": "D3/D4",   "phys_leds": (20, 21)},
    5: {"label": "STBY",        "leds": (8,9), "pins": "D23/D24", "phys_leds": (12, 13)},
    6: {"label": "PROG",        "leds": (10,11), "pins": "D5/D6",   "phys_leds": (22, 23)},
    7: {"label": "KEY REL",     "leds": (12,13), "pins": "D21/D22", "phys_leds": (10, 11)},
    8: {"label": "RSTRT",       "leds": (14,15), "pins": "D7/D8",   "phys_leds": (24, 25)},
    9: {"label": "OPR ERR",     "leds": (16,17), "pins": "D19/D20", "phys_leds": (8, 9)},
    10: {"label": "TRKR",        "leds": (18,19), "pins": "D9/D10",  "phys_leds": (26, 27)},
    11: {"label": "PRIO DISP",   "leds": (20,21), "pins": "D17/D18", "phys_leds": (6, 7)},
    12: {"label": "ALT",         "leds": (22,23), "pins": "D11/D12", "phys_leds": (0, 1)},
    13: {"label": "NO DAP",      "leds": (24,25), "pins": "D15/D16", "phys_leds": (4, 5)},
    14: {"label": "VEL",         "leds": (26,27), "pins": "D13/D14", "phys_leds": (2, 3)},
}

# Map logical leds to physical LED indices
LED_MAP = []
for key, value in sorted(INDICATORS.items()):
    print(f"Processing indicator {key} with phys_leds {value['phys_leds']}")
    LED_MAP.extend(value["phys_leds"])

print(f"LED_MAP: {LED_MAP}")

# --- 2. Keypad Matrix Configuration ---
ROW_PINS = (board.GP27, board.GP26, board.GP15, board.GP14)
COL_PINS = (board.GP4, board.GP5, board.GP6, board.GP7, board.GP8)

KEYMAP = (
    Keycode.C, Keycode.NINE,  Keycode.EIGHT, Keycode.SEVEN, Keycode.KEYPAD_PLUS,
    Keycode.P, Keycode.SIX,   Keycode.FIVE,  Keycode.FOUR,  Keycode.MINUS,
    Keycode.K, Keycode.THREE, Keycode.TWO,   Keycode.ONE,   Keycode.ZERO,
    Keycode.E, Keycode.R,     None,          Keycode.V,     Keycode.N,
)

def led_white(pixels):
    pixels.fill(WHITE)
    pixels.show()

def led_clear(pixels):
    pixels.fill(CLEAR)
    pixels.show()

def color_chase(pixels, color, wait):
    """Lights up one pixel at a time sequentially along the strip."""
    for i in range(NUM_LEDS):
        pixels[LED_MAP[i]] = color
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

def rainbow_cycle(pixels, wait):
    """Smoothly cycles a rainbow across the entire strip."""
    for j in range(256):
        for i in range(NUM_LEDS):
            pixel_index = (i * 256 // NUM_LEDS) + j
            pixels[LED_MAP[i]] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)

# Primary color definitions (Red, Green, Blue)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CLEAR = (0, 0, 0)
WHITE = (255, 255, 255)

def led_test_pattern(pixels):
    color_chase(pixels, RED, 0.05)
    color_chase(pixels, GREEN, 0.05)
    color_chase(pixels, BLUE, 0.05)
    rainbow_cycle(pixels, 0.01)

print("Starting NeoPixel loop on GP2...")

# while True:
#     # 1. Run solid color fills
#     color_chase(RED, 0.05)
#     color_chase(GREEN, 0.05)
#     color_chase(BLUE, 0.05)
#
#     # 2. Run a rainbow animation loop
#     print("Running rainbow cycle...")
#     for _ in range(3):  # Repeat rainbow 3 times
#         rainbow_cycle(0.01)
#
#     # Clear the strip before repeating
#     pixels.fill(CLEAR)
#     pixels.show()
#     time.sleep(1)


keys = keypad.KeyMatrix(row_pins=ROW_PINS, column_pins=COL_PINS, columns_to_anodes=True)

# --- 3. USB HID Setup ---
kbd = Keyboard(usb_hid.devices)
led_endpoint = None

# Locate custom HID device
for device in usb_hid.devices:
    print(f"Found USB HID device: {device} usage_page={device.usage_page} usage={device.usage}")
    if device.usage_page == 0xFF00 and device.usage == 0x01:
        led_endpoint = device
        print("Found custom HID device:", device)
        break

led_test_pattern(pixels)
time.sleep(1)
led_white(pixels)
time.sleep(1)
led_clear(pixels)


while True:
    # A. Process keypad events
    event = keys.events.get()
    if event:
        print(f"Key event: {event}")
        keycode = KEYMAP[event.key_number]
        if keycode is not None:
            if event.pressed:
                kbd.press(keycode)
            else:
                kbd.release(keycode)

    # B. Process incoming 8-byte command packets
    if led_endpoint:
        packet = led_endpoint.get_last_received_report()
        if packet:
            cmd = packet[0]
            print(f"Received cmd {cmd} packet: {packet}")
            if cmd == CMD_SET_BRIGHTNESS:
                # Map 0..255 byte to 0.0..1.0 float
                pixels.brightness = packet[1] / 255.0
                commit = packet[2]
                print(f"Set brightness to {pixels.brightness} commit={commit}")
                if commit:
                    pixels.show()

            elif cmd == CMD_SET_RANGE:
                offset = packet[1]
                count = packet[2]
                color = (packet[3], packet[4], packet[5])
                commit = packet[6]

                print(f"Set LED range offset={offset} count={count} color={color} commit={commit}") 

                if offset < NUM_LEDS and count > 0:
                    end = min(offset + count, NUM_LEDS)
                    for i in range(offset, end):
                        print(f"Setting LED{i} ({LED_MAP[i]}) to color {color}")
                        pixels[LED_MAP[i]] = color
                    if commit:
                        pixels.show()

            elif cmd == CMD_SHOW:
    
                pixels.show()

    time.sleep(0.005)
