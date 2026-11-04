# Apollo DSKY 19-Key Matrix Scanner Code

import board
import keypad
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# 1. Initialize the global USB HID Keyboard interface
kbd = Keyboard(usb_hid.devices)

# 2. Define your exact 5x4 pin configuration
# Rows = 5 pins (GP4-GP8), Columns = 4 pins (GP9-GP12)
matrix = keypad.KeyMatrix(
    row_pins=(board.GP4, board.GP5, board.GP6, board.GP7, board.GP8),
    column_pins=(board.GP9, board.GP10, board.GP11, board.GP12),
    columns_to_anodes=False  # Set to True if your diodes point from Col to Row
)

# 3. Create a 20-element keymap array matching your physical rows/cols layout.
# Note: Position 19 is left as None to perfectly accommodate your 19 physical keys.
KEY_MAP = [
    # Row 1 (GP4) -> Cols GP9, GP10, GP11, GP12
    Keycode.ONE,       Keycode.TWO,       Keycode.THREE,     Keycode.A,
    
    # Row 2 (GP5) -> Cols GP9, GP10, GP11, GP12
    Keycode.FOUR,      Keycode.FIVE,      Keycode.SIX,       Keycode.B,
    
    # Row 3 (GP6) -> Cols GP9, GP10, GP11, GP12
    Keycode.SEVEN,     Keycode.EIGHT,     Keycode.NINE,      Keycode.C,
    
    # Row 4 (GP7) -> Cols GP9, GP10, GP11, GP12
    Keycode.ZERO,      Keycode.UP_ARROW,  Keycode.DOWN_ARROW,Keycode.D,
    
    # Row 5 (GP8) -> Cols GP9, GP10, GP11, GP12 (19 keys total)
    Keycode.ENTER,     Keycode.ESCAPE,     Keycode.KEYPAD_MINUS, None
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
