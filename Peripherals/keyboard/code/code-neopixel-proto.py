#
# Key Matrix Controller with an attached string of addressable (neopixel) LEDs
#
import time
import board
import neopixel
import usb_hid
from adafruit_hid.keyboard import Keyboard

print("RecreateApollo DSKY Keyboard Controller")
print("Initializing LEDs...")

# --- Neopixel LED Setup ---
# Match this to your total physical strip length
PIXEL_PIN = board.GP2
NUM_LEDS = 28
PER_LED_UPDATE_MAX = 20

RED_COLOR = (255, 0, 0)
GREEN_COLOR = (0, 255, 0)
BLUE_COLOR = (0, 0, 255)
CLEAR_COLOR = (0, 0, 0)
INIT_COLOR = (40, 40, 40)

pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_LEDS, auto_write=False, brightness=0.3)
pixels.fill(INIT_COLOR)
pixels.show()

# --- USB HID Initialization ---
kbd = Keyboard(usb_hid.devices)
led_endpoint = None

# Locate custom HID device
for device in usb_hid.devices:
    print(f"Found USB HID device: {device} usage_page={device.usage_page} usage={device.usage}")
    if device.usage_page == 0xFF00 and device.usage == 0x01:
        led_endpoint = device
        print("Found custom HID device:", device)
        break

print("Keyboard & LED HID Controller Ready!")

def dump_request_packet(packet):
    if packet is not None:
        hex_dump = " ".join(f"{b:02X}" for b in packet)
        print(f"Received {len(packet)} bytes: {hex_dump}")
        print("<End of packet>")

def print_led_update(offset, i, r, g, b):
    print(f"Updating LED at index {offset + i} to color ({r}, {g}, {b})")

while True:
    if led_endpoint:
        packet = led_endpoint.get_last_received_report()

        if packet:
            dump_request_packet(packet)
            # Byte 0: Starting LED index (Offset)
            # Byte 1: Number of LEDs to update in this packet (max 20)
            # Bytes 2..61: Sequential R, G, B values
            offset = packet[0]
            count = packet[1]

            # Prevent out-of-bounds errors
            max_updatable = min(count, PER_LED_UPDATE_MAX, NUM_LEDS - offset)

            print(f"Updating LEDs starting at offset {offset} with count {max_updatable}")
            for i in range(max_updatable):
                base_idx = 2 + (i * 3)
                r = packet[base_idx]
                g = packet[base_idx + 1]
                b = packet[base_idx + 2]
                print_led_update(offset, i, r, g, b)
                pixels[offset + i] = (r, g, b)

            pixels.show()

    time.sleep(0.005)  # 5ms polling for smooth animations
