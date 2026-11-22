# Test script for controlling the LED interface via HID

import hid
import struct
import argparse

VENDOR_ID = 0x2e8A  # Standard Adafruit/CircuitPython VID
PRODUCT_ID = 0x10B0  # Standard Adafruit/CircuitPython PID


def init_args():
    parser = argparse.ArgumentParser(description="Test LED rainbow pattern")
    parser.add_argument("--offset", type=int, default=0, help="Starting LED offset")
    parser.add_argument("--count", type=int, default=28, help="Number of LEDs to update")
    parser.add_argument("--color", type=str, default="255,0,0", help="Comma-separated RGB color for the LEDs")
    parser.add_argument("--pattern", type=str, default="rainbow", help="LED pattern to display")
    return parser.parse_args()


def find_led_interface():
    devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
    if not devices:
        print("No devices found with VID:PID", hex(VENDOR_ID), hex(PRODUCT_ID))
        return None
    
    for dev in devices:
        # On Ubuntu hidraw, Interface '3' is our composite HID device with the LED interface
        if dev['interface_number'] == 3:
            print(f"Found LED interface at path: {dev['path']}")
            return dev['path']
            
    # Fallback: return the first matching HID path for this board
    print(f"LED interface not found, falling back to first matching HID path {devices[0]['path']}.")
    return devices[0]['path']

def set_leds(dev, offset: int, rgb_list: list[tuple[int, int, int]]):
    """
    Sends a list of (R, G, B) tuples starting at `offset`.
    Automatically splits into chunks of 20 LEDs to fit 64-byte HID reports.
    """
    report_id = 4
    chunk_size = 20  # 2 header bytes + (20 * 3 color bytes) = 62 bytes <= 64

    print(f"Setting LEDs starting at offset {offset} with {len(rgb_list)} colors")
    for i in range(0, len(rgb_list), chunk_size):
        chunk = rgb_list[i:i + chunk_size]
        current_offset = offset + i
        count = len(chunk)

        # Pack Offset and Count
        payload = bytearray(struct.pack("<BB", current_offset, count))
        
        # Append R, G, B bytes for each LED in the chunk
        for r, g, b in chunk:
            payload.extend(struct.pack("<BBB", r, g, b))

        # Pad the payload to exactly 64 bytes, then prepend Report ID (65 bytes total)
        padded_payload = payload + b'\x00' * (63 - len(payload))
        packet = bytes([report_id]) + padded_payload
        
        assert len(packet) == 64, f"Unexpected packet length: {len(packet)}"
        dev.write(packet)

if __name__ == "__main__":
    
    args = init_args()
    
    path = find_led_interface()
    if not path:
        print("Error: LED HID interface not found. Did you hard-reset the board after updating boot.py?")
        exit(1)

    print(f"Opening LED interface at path: {path}")
    device = hid.device()
    try:
        device.open_path(path)
    except Exception as e:
        print(f"Failed to open LED interface at path {path}: {e}")
        exit(1)

    # Parse the color argument into an (R, G, B) tuple
    color = tuple(map(int, args.color.split(',')))
    if len(color) != 3:
        print("Error: --color must be in the format R,G,B")
        exit(1)
        
    colors = [color] * args.count
    set_leds(device, offset=args.offset, rgb_list=colors)
    print(f"Updated {len(colors)} LEDs starting at index {args.offset}.")
    
    device.close()
