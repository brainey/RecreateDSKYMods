# Apollo DSKY 19-Key Matrix Scanner Code

import board
import keypad
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# 1. Initialize the global USB HID Keyboard interface
kbd = Keyboard(usb_hid.devices)

# 2. Define your exact 5x4 pin configuration
# Due to internal pull-up problem in the RP2350, will active low for the matrix scanning
# Rows = 4 pins (GP9-GP12), Columns = 5 pins (GP4-GP8)
matrix = keypad.KeyMatrix(
    row_pins=(board.GP9, board.GP10, board.GP11, board.GP12),
    column_pins=(board.GP4, board.GP5, board.GP6, board.GP7, board.GP8),
    columns_to_anodes=True  # Set to True if your diodes point from Col to Row
)

# 3. Create a 20-element keymap array matching your physical rows/cols layout.
# Note: Position 19 is left as None to perfectly accommodate your 19 physical keys.
KEY_MAP = [
    # Row 1 (GP9) -> Cols GP4, GP5, GP6, GP7, GP8
    Keycode.C,       Keycode.NINE,       Keycode.EIGHT,     Keycode.SEVEN,      Keycode.KEYPAD_PLUS,
    
    # Row 2 (GP10) -> Cols GP4, GP5, GP6, GP7, GP8
    Keycode.P,       Keycode.SIX,       Keycode.FIVE,       Keycode.FOUR,       Keycode.MINUS,
    
    # Row 3 (GP11) -> Cols GP4, GP5, GP6, GP7, GP8
    Keycode.K,       Keycode.THREE,     Keycode.TWO,        Keycode.ONE,        Keycode.ZERO,
    
    # Row 4 (GP12) -> Cols GP4, GP5, GP6, GP7, GP8
    Keycode.E,   Keycode.R,    None,               Keycode.V,          Keycode.N,
]

print("Apollo DSKY 19-Key Matrix Scanner Initialized...")

# 4. Main Execution Event Loop
while True:
    event = matrix.events.get()
    if event:
        # Get the linear key number (0 to 19)
        key_number = event.key_number
        keycode = KEY_MAP[key_number]
        
        # Skip processing if the event hits an unmapped/empty layout position
        if keycode is None:
            continue
            
        if event.pressed:
            kbd.press(keycode)
            print(f"Key Pressed: Index {key_number}")
        elif event.released:
            kbd.release(keycode)
