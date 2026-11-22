import board
import keypad
import neopixel
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# --- 1. LED Configuration ---
LED_PIN = board.GP2       # Update to your RP2350-Zero data pin
NUM_LEDS = 28            # Update to your total DSKY LED count
pixels = neopixel.NeoPixel(LED_PIN, NUM_LEDS, brightness=0.3, auto_write=False)

# --- 2. Keypad Matrix Configuration (Example: 3x7 DSKY Matrix) ---
ROW_PINS = (board.GP27, board.GP26, board.GP15, board.GP14)
COL_PINS = (board.GP4, board.GP5, board.GP6, board.GP7, board.GP8)

KEYMAP = (
    # Row 1 (GP9) -> Cols GP4, GP5, GP6, GP7, GP8
    Keycode.C,       Keycode.NINE,       Keycode.EIGHT,     Keycode.SEVEN,      Keycode.KEYPAD_PLUS,
    
    # Row 2 (GP10) -> Cols GP4, GP5, GP6, GP7, GP8
    Keycode.P,       Keycode.SIX,       Keycode.FIVE,       Keycode.FOUR,       Keycode.MINUS,
    
    # Row 3 (GP11) -> Cols GP4, GP5, GP6, GP7, GP8
    Keycode.K,       Keycode.THREE,     Keycode.TWO,        Keycode.ONE,        Keycode.ZERO,
    
    # Row 4 (GP12) -> Cols GP4, GP5, GP6, GP7, GP8
    Keycode.E,   Keycode.R,    None,               Keycode.V,          Keycode.N,
)

def dump_request_packet(packet):
    if packet is not None:
        hex_dump = " ".join(f"{b:02X}" for b in packet)
        print(f"Received {len(packet)} bytes: {hex_dump}")
        print("<End of packet>")

def print_led_update(offset, i, r, g, b):
    print(f"Updating LED at index {offset + i} to color ({r}, {g}, {b})")

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

while True:
    # A. Process any queued keypad events (non-blocking)
    event = keys.events.get()
    if event:
        print(f"Key event: {event}")
        keycode = KEYMAP[event.key_number]
        if keycode is not None:
            if event.pressed:
                kbd.press(keycode)
            else:
                kbd.release(keycode)

    # B. Process incoming LED packets from Ubuntu host
    if led_endpoint:
        packet = led_endpoint.get_last_received_report()
        if packet:
            offset = packet[0]
            count = packet[1]
            # commit = packet[62]
            dump_request_packet(packet)
            print(f"LED update: offset={offset}, count={count}")
            
            if offset < NUM_LEDS:
                max_leds = min(count, 20, NUM_LEDS - offset)
                for i in range(max_leds):
                    base = 2 + (i * 3)
                    pixels[offset + i] = (
                        packet[base],
                        packet[base + 1],
                        packet[base + 2],
                    )
                # if commit:
                #     pixels.show()
                pixels.show()
