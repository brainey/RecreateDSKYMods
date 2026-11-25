"""DSKY v2 Keyboard Assembly (Rev V1.1) test script for Raspberry Pi Pico 2 W.

Hardware connections (Keyboard Assembly J1 -> Raspberry Pi Pico 2 W):
  J1 Pin 1 (/+5V)         -> Pin 40 (VBUS) or external 5V supply
  J1 Pin 2 (/+3V3)        -> Pin 36 (3V3 OUT)
  J1 Pin 3 (/SDA)         -> Pin 6  (GP4, I2C0 SDA)
  J1 Pin 4 (/SCL)         -> Pin 7  (GP5, I2C0 SCL)
  J1 Pin 5 (/INT)         -> Pin 9  (GP6, active-low with R12 10k pull-up)
  J1 Pin 6 (/KEYLHT_DATA) -> Pin 10 (GP7, to U2 74AHCT1G125 -> R21 -> D1)
  J1 Pin 7 (GND)          -> Pin 8  (GND)
"""

import select
import sys
import time
from machine import I2C, Pin
import neopixel

# --- Hardware configuration ---
I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 100_000
TCA_ADDR = 0x34          # TCA8418RTWR fixed 7-bit I2C address
INT_PIN = 6              # J1 Pin 5 (/INT, active-low) -> Pico Pin 9
LED_PIN = 7              # J1 Pin 6 (/KEYLHT_DATA)     -> Pico Pin 10
LED_COUNT = 19           # D1..D19 SK6812MINI-E-012 (GRB)
DEFAULT_BRIGHTNESS = 64  # 25% default (~170 mA max on white)
LED_TIMING = (300, 900, 850, 350)  # SK6812MINI-E-012 (T0H, T0L, T1H, T1L) ns

# TCA8418 registers (TI SCPS215G Table 9)
REG_CFG = 0x01
REG_INT_STAT = 0x02
REG_KEY_LCK_EC = 0x03
REG_KEY_EVENT_A = 0x04
REG_KP_GPIO1 = 0x1D
REG_KP_GPIO2 = 0x1E
REG_KP_GPIO3 = 0x1F
REG_DEBOUNCE_DIS1 = 0x29
REG_GPIO_PULL1 = 0x2C

# TCA8418 key code (row*10 + col + 1) -> (Switch, Label, LED ref, serpentine LED index)
KEYS = {
    1:  ("SW1",  "+",       "D3",  4),
    2:  ("SW2",  "7",       "D6",  5),
    3:  ("SW3",  "8",       "D9",  10),
    4:  ("SW4",  "9",       "D12", 11),
    5:  ("SW5",  "CLR",     "D15", 16),
    11: ("SW6",  "-",       "D4",  3),
    12: ("SW7",  "4",       "D7",  6),
    13: ("SW8",  "5",       "D10", 9),
    14: ("SW9",  "6",       "D13", 12),
    15: ("SW10", "PRO",     "D16", 15),
    21: ("SW11", "0",       "D5",  2),
    22: ("SW12", "1",       "D8",  7),
    23: ("SW13", "2",       "D11", 8),
    24: ("SW14", "3",       "D14", 13),
    25: ("SW15", "KEY REL", "D17", 14),
    31: ("SW16", "VERB",    "D1",  0),
    32: ("SW17", "NOUN",    "D2",  1),
    33: ("SW18", "ENTR",    "D18", 17),
    34: ("SW19", "RSET",    "D19", 18),
}
CHAIN = sorted(KEYS.values(), key=lambda item: item[3])

COLOR_MAP = {
    "R": (255, 0, 0),
    "G": (0, 255, 0),
    "B": (0, 0, 255),
    "W": (255, 255, 255),
    "OFF": (0, 0, 0),
}
COLOR_ALIASES = {
    "R": "R", "RED": "R",
    "G": "G", "GREEN": "G",
    "B": "B", "BLUE": "B",
    "W": "W", "WHITE": "W",
    "OFF": "OFF",
}


def _parse_brightness(text):
    """Parse '0..255' or '0%..100%' into clamped 0..255 int, or None."""
    s = str(text).strip()
    if not s:
        return None
    is_pct = s.endswith("%")
    if is_pct:
        s = s[:-1].strip()
    try:
        val = int(s)
    except ValueError:
        return None
    if is_pct:
        val = (val * 255) // 100
    return max(0, min(255, val))


def _scale_rgb(rgb, brightness):
    """Scale an (R, G, B) tuple by 0..255 brightness."""
    return (
        (rgb[0] * brightness) // 255,
        (rgb[1] * brightness) // 255,
        (rgb[2] * brightness) // 255,
    )


class KeypadTester:
    """Interactive test harness for Keyboard Assembly TCA8418 + SK6812MINI-E LEDs."""

    def __init__(self, brightness=DEFAULT_BRIGHTNESS):
        self.np = neopixel.NeoPixel(
            Pin(LED_PIN, Pin.OUT), LED_COUNT, bpp=3, timing=LED_TIMING
        )
        self.int_pin = Pin(INT_PIN, Pin.IN, Pin.PULL_UP)
        self.i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)

        self.brightness = max(0, min(255, int(brightness)))
        self.mode = "KEY"
        self.color_name = "OFF"
        self.tested = set()
        self.held = set()
        self._announced_all = False
        self._fill((0, 0, 0))

    def _write_reg(self, reg, val):
        self.i2c.writeto_mem(TCA_ADDR, reg, bytes([val & 0xFF]))

    def _read_reg(self, reg):
        return self.i2c.readfrom_mem(TCA_ADDR, reg, 1)[0]

    def init_tca8418(self):
        """Verify TCA8418 on I2C0 and configure 4x5 keypad matrix + interrupts."""
        found = self.i2c.scan()
        if TCA_ADDR not in found:
            hex_list = [f"0x{a:02X}" for a in found]
            raise RuntimeError(
                f"TCA8418 not found at 0x{TCA_ADDR:02X} (found: {hex_list}). "
                f"Check J1: Pin 2->3V3, Pin 3(SDA)->GP{SDA_PIN}, Pin 4(SCL)->GP{SCL_PIN}, Pin 7->GND."
            )

        # Matrix: ROW0..3 (0x0F) x COL0..4 (0x1F); unused pins remain pulled-up GPIO inputs
        self._write_reg(REG_KP_GPIO1, 0x0F)
        self._write_reg(REG_KP_GPIO2, 0x1F)
        self._write_reg(REG_KP_GPIO3, 0x00)
        for offset in range(3):
            self._write_reg(REG_DEBOUNCE_DIS1 + offset, 0x00)  # debounce ON
            self._write_reg(REG_GPIO_PULL1 + offset, 0x00)     # pull-ups ON

        r1 = self._read_reg(REG_KP_GPIO1)
        r2 = self._read_reg(REG_KP_GPIO2)
        if (r1, r2) != (0x0F, 0x1F):
            raise RuntimeError(f"TCA8418 readback mismatch: 0x{r1:02X}, 0x{r2:02X}")

        while self._read_reg(REG_KEY_EVENT_A):
            pass  # flush stale FIFO events
        self._write_reg(REG_INT_STAT, 0x1F)
        self._write_reg(REG_CFG, 0x11)  # INT_CFG | KE_IEN

        int_idle = "LOW (check J1 Pin 5 / R12!)" if self.int_pin.value() == 0 else "HIGH (OK)"
        print(f"TCA8418 OK at 0x{TCA_ADDR:02X} | /INT idle: {int_idle}")

    def write_leds(self):
        """Latch pixel buffer and honor SK6812MINI-E >200 us reset time."""
        self.np.write()
        time.sleep_us(350)

    def _fill(self, color):
        for i in range(LED_COUNT):
            self.np[i] = color
        self.write_leds()

    def render(self):
        """Update LEDs for current mode, brightness, and pressed/tested keys."""
        b = self.brightness
        if self.mode == "KEY":
            dim_blue = (0, max(1, b // 16) if b else 0, max(1, b // 6) if b else 0)
            passed_green = (0, b, b // 4)
            held_white = (b, b, b)
            for code, info in KEYS.items():
                led_idx = info[3]
                if code in self.held:
                    self.np[led_idx] = held_white
                elif code in self.tested:
                    self.np[led_idx] = passed_green
                else:
                    self.np[led_idx] = dim_blue
            self.write_leds()
            return

        # SOLID color mode: fill base color, flash white (or green on white) for held keys
        base = _scale_rgb(COLOR_MAP[self.color_name], b)
        for i in range(LED_COUNT):
            self.np[i] = base
        contrast = (0, b, 0) if self.color_name == "W" else (b, b, b)
        for code in self.held:
            if code in KEYS:
                self.np[KEYS[code][3]] = contrast
        self.write_leds()

    def set_brightness(self, val):
        """Set brightness (0..255 or 'NN%') and re-render."""
        parsed = _parse_brightness(val)
        if parsed is None:
            print(f"Invalid brightness '{val}'. Use 0-255 or 0%-100%.")
            return
        self.brightness = parsed
        if self.brightness > 178:
            print(
                f"Note: brightness {self.brightness}/255 (>70%); "
                "SK6812MINI-E-012 datasheet recommends <=70% on full white."
            )
        self.render()
        print(f"Keypad brightness: {self.brightness}/255 ({(self.brightness * 100) // 255}%)")

    def set_color(self, name):
        """Switch to SOLID color mode (R, G, B, W, OFF)."""
        key = COLOR_ALIASES.get(str(name).strip().upper())
        if key is None:
            print(f"Unknown color '{name}'. Use R, G, B, W, or OFF.")
            return
        self.mode = "SOLID"
        self.color_name = key
        self.render()
        print(f"Keypad color: {key} @ {self.brightness}/255")

    def set_key_mode(self, reset=False):
        """Return to interactive key-test mode; optionally clear pass tracking."""
        self.mode = "KEY"
        if reset:
            self.tested.clear()
            self.held.clear()
            self._announced_all = False
            print("Keypad pass tracking reset (0/19).")
        else:
            print(f"Keypad interactive key mode ({len(self.tested)}/19 tested).")
        self.render()

    def chase(self):
        """Step one LED at a time in serpentine data-chain order (D1..D19)."""
        print("Keypad serpentine LED chase (D1 -> D19):")
        b = self.brightness or 32
        chase_color = (0, b, b // 3)
        for _, label, led_ref, idx in CHAIN:
            for i in range(LED_COUNT):
                self.np[i] = (0, 0, 0)
            self.np[idx] = chase_color
            self.write_leds()
            print(f"  LED[{idx:02d}] {led_ref:<3} ({label})")
            time.sleep_ms(110)
        self.render()

    def self_test(self):
        """Flash R/G/B/W and run serpentine chase before entering key mode."""
        print("Keypad LED R/G/B/W + serpentine chase...")
        b = self.brightness
        for name in ("R", "G", "B", "W"):
            scale = min(b, 178) if name == "W" else b
            print(f"  All LEDs: {name}")
            self._fill(_scale_rgb(COLOR_MAP[name], scale))
            time.sleep_ms(300)
        self.chase()

    def poll_keys(self):
        """Drain pending TCA8418 FIFO events and update corresponding LEDs."""
        int_low = self.int_pin.value() == 0
        count = self._read_reg(REG_KEY_LCK_EC) & 0x0F
        if not (count or int_low):
            return 0

        events = 0
        int_low = int_low or (self.int_pin.value() == 0)
        while True:
            evt = self._read_reg(REG_KEY_EVENT_A)
            if evt == 0:
                break
            events += 1
            pressed = bool(evt & 0x80)
            code = evt & 0x7F
            if code in KEYS:
                sw, label, led_ref, led_idx = KEYS[code]
                action = "PRESS  " if pressed else "RELEASE"
                int_tag = "INT=OK" if int_low else "INT=HIGH! (check J1 Pin 5)"
                if pressed:
                    self.held.add(code)
                else:
                    self.held.discard(code)
                    self.tested.add(code)
                self.render()
                print(
                    f"[{len(self.tested):2d}/19] {action} {sw:<4} '{label:<7}' "
                    f"(code {code:2d}, {led_ref:<3}->LED[{led_idx:02d}]) [{int_tag}]"
                )
                if not self._announced_all and len(self.tested) == len(KEYS):
                    self._announced_all = True
                    print("\n*** ALL 19 KEYS PASSED! ***\n")
            else:
                print(f"Unexpected key event: 0x{evt:02X} (code {code})")

        self._write_reg(REG_INT_STAT, 0x1F)
        return events

    def handle_command(self, cmd_str):
        """Process one text command. Returns False to quit, True otherwise."""
        raw = cmd_str.strip()
        if not raw:
            return True
        upper = raw.upper()
        parts = upper.split(None, 1)
        verb = parts[0]
        arg = parts[1] if len(parts) > 1 else ""

        if verb in ("Q", "QUIT", "EXIT"):
            return False
        if verb in ("HELP", "?"):
            print_help()
        elif verb == "KEY":
            self.set_key_mode(reset=False)
        elif verb == "RESET":
            self.set_key_mode(reset=True)
        elif verb == "CHASE":
            self.chase()
        elif verb in COLOR_ALIASES:
            self.set_color(verb)
        elif verb in ("BRI", "BRIGHT", "BRIGHTNESS") and arg:
            self.set_brightness(arg)
        elif _parse_brightness(upper) is not None:
            self.set_brightness(upper)
        else:
            print(f"Unknown keypad command '{raw}'. Type HELP for options.")
        return True

    def off(self):
        """Turn off all keypad LEDs immediately."""
        self.mode = "SOLID"
        self.color_name = "OFF"
        self.held.clear()
        self._fill((0, 0, 0))


def print_help():
    """Print available Thonny shell commands for keypad testing."""
    print(
        "Keypad commands: R | G | B | W | OFF | BRI <0-255 or %> | "
        "KEY | RESET | CHASE | HELP | Q"
    )


def run(run_self_test=True):
    """Initialize keypad hardware and run interactive key + LED test loop."""
    tester = KeypadTester()
    poll_obj = select.poll()
    poll_obj.register(sys.stdin, select.POLLIN)

    try:
        tester.init_tca8418()
        if run_self_test:
            tester.self_test()
        tester.set_key_mode(reset=False)
        print_help()
        print("Press keys (or type command + Enter; Q to quit)...")

        while True:
            tester.poll_keys()
            if poll_obj.poll(0):
                line = sys.stdin.readline()
                if not line or not tester.handle_command(line):
                    break
            time.sleep_ms(10)
    except KeyboardInterrupt:
        print("\nKeypad test interrupted.")
    finally:
        tester.off()
        print("Keypad LEDs OFF.")


if __name__ == "__main__":
    run()
