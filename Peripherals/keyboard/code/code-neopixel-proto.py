import board
import neopixel
import usb_hid

PIXEL_PIN = board.GP2
NUM_LEDS = 8

# Match this to your total physical strip length
pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_LEDS, auto_write=False, brightness=0.3)

# locate custom HID device
for devuce in usb_hid.devices:
    print(f"Found USB HID device: {devuce} usage_page={devuce.usage_page} usage={devuce.usage}")
    if devuce.usage_page == 0xFF00 and devuce.usage == 0x01:
        print("Found custom HID device:", devuce)
        hid_out_device = devuce

print("HID out device:", dir(hid_out_device))

RED_COLOR = (255, 0, 0)
GREEN_COLOR = (0, 255, 0)
BLUE_COLOR = (0, 0, 255)
CLEAR_COLOR = (0, 0, 0)
INIT_COLOR = (40, 40, 40)
pixels.fill(INIT_COLOR)

while True:
    # Read the 5-byte report from ID 1
    data = hid_out_device.get_last_received_report(1)
    
    if data is not None and len(data) >= 5:
        offset = data[0]
        count = data[1]
        r, g, b = data[2], data[3], data[4]
        
        # Calculate bound safety to prevent index errors
        end_index = min(offset + count, NUM_LEDS)
        
        # Update only the targeted range of LEDs
        for i in range(offset, end_index):
            pixels[i] = (r, g, b)
            
        # Push changes out to the WS2812b string
        pixels.show()
