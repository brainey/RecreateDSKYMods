import time
import board
import keypad
import neopixel
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# --- 1. LED Configuration ---
LED_PIN = board.GP2
NUM_LEDS = 28
pixels = neopixel.NeoPixel(LED_PIN, NUM_LEDS, brightness=0.3, auto_write=False)

# Command Opcodes
CMD_SET_BRIGHTNESS = 0x01
CMD_SET_RANGE      = 0x02
CMD_SHOW           = 0x03

# --- 2. Keypad Matrix Configuration ---
ROW_PINS = (board.GP27, board.GP26, board.GP15, board.GP14)
COL_PINS = (board.GP4, board.GP5, board.GP6, board.GP7, board.GP8)

KEYMAP = (
    Keycode.C, Keycode.NINE,  Keycode.EIGHT, Keycode.SEVEN, Keycode.KEYPAD_PLUS,
    Keycode.P, Keycode.SIX,   Keycode.FIVE,  Keycode.FOUR,  Keycode.MINUS,
    Keycode.K, Keycode.THREE, Keycode.TWO,   Keycode.ONE,   Keycode.ZERO,
    Keycode.E, Keycode.R,     None,          Keycode.V,     Keycode.N,
)

keys = keypad.KeyMatrix(row_pins=ROW_PINS, column_pins=COL_PINS, columns_to_anodes=True)

# --- 3. USB HID Setup ---
kbd = Keyboard(usb_hid.devices)
led_endpoint = next(
    (d for d in usb_hid.devices if d.usage_page == 0xFF00 and d.usage == 0x01),
    None,
)

while True:
    # A. Process keypad events
    event = keys.events.get()
    if event:
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

            if cmd == CMD_SET_BRIGHTNESS:
                # Map 0..255 byte to 0.0..1.0 float
                pixels.brightness = packet[1] / 255.0
                if packet[2]:
                    pixels.show()

            elif cmd == CMD_SET_RANGE:
                offset = packet[1]
                count = packet[2]
                color = (packet[3], packet[4], packet[5])
                commit = packet[6]

                if offset < NUM_LEDS and count > 0:
                    end = min(offset + count, NUM_LEDS)
                    for i in range(offset, end):
                        pixels[i] = color
                    if commit:
                        pixels.show()

            elif cmd == CMD_SHOW:
                pixels.show()

    time.sleep(0.005)
