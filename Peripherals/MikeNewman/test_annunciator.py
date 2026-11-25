"""DSKY v2 Annunciator Assembly (Rev V1.1) test script for Raspberry Pi Pico 2 W.

Hardware connections (Annunciator Assembly J1 -> Raspberry Pi Pico 2 W):
  J1 Pin 1 (/+5V)           -> Pin 40 (VBUS) or external 5V supply
  J1 Pin 2 (/+3V3 PROVISION)-> Unconnected (NC on PCB)
  J1 Pin 3 (ANN_DATA)       -> Pin 1  (GP0, to R10/U1 74AHCT1G125 -> R11 -> D11)
  J1 Pin 4 & 5 (GND)        -> Pin 3  (GND) / common breadboard GND
"""

import time
from machine import Pin
import neopixel

# --- Hardware configuration ---
LED_PIN = 0              # J1 Pin 3 (ANN_DATA) -> Pico Pin 1 (GP0)
LED_COUNT = 28           # 14 annunciator windows x 2 WS2813B-V5 LEDs each (GRB)
DEFAULT_BRIGHTNESS = 50  # ~20% default (~270 mA max on white, USB-safe)
LED_TIMING = (300, 800, 800, 700)  # WS2813B-V5 (T0H, T0L, T1H, T1L) ns

# Physical data-chain order (indices 0..27) verified against Annunciator_Assembly.net
WINDOWS = (
    ("ALT",         "D11/D12", (0, 1)),
    ("VEL",         "D13/D14", (2, 3)),
    ("NO DAP",      "D15/D16", (4, 5)),
    ("PRIO DISP",   "D17/D18", (6, 7)),
    ("OPR ERR",     "D19/D20", (8, 9)),
    ("KEY REL",     "D21/D22", (10, 11)),
    ("STBY",        "D23/D24", (12, 13)),
    ("NO ATT",      "D25/D26", (14, 15)),
    ("UPLINK ACTY", "D27/D28", (16, 17)),
    ("TEMP",        "D1/D2",   (18, 19)),
    ("GIM LOCK",    "D3/D4",   (20, 21)),
    ("PROG",        "D5/D6",   (22, 23)),
    ("RSTRT",       "D7/D8",   (24, 25)),
    ("TRKR",        "D9/D10",  (26, 27)),
)

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


class AnnunciatorTester:
    """Interactive color, brightness, and window tester for 28 WS2813B-V5 LEDs."""

    def __init__(self, brightness=DEFAULT_BRIGHTNESS):
        self.np = neopixel.NeoPixel(
            Pin(LED_PIN, Pin.OUT), LED_COUNT, bpp=3, timing=LED_TIMING
        )
        self.brightness = max(0, min(255, int(brightness)))
        self.color_name = "OFF"
        self.single_window = None  # 1..14 when isolating a single window
        self.off()

    def write_leds(self):
        """Latch pixel buffer and honor WS2813B-V5 >280 us reset time."""
        self.np.write()
        time.sleep_us(350)

    def _rgb(self):
        return _scale_rgb(COLOR_MAP[self.color_name], self.brightness)

    def _warn_if_high_current(self):
        if self.color_name == "W" and self.brightness > 100 and self.single_window is None:
            est_ma = int((28 * 48 * self.brightness) / 255)
            print(
                f"Warning: all 28 LEDs white @ {self.brightness}/255 can draw ~{est_ma} mA; "
                "use an external 5V supply (with common GND) above ~100/255."
            )

    def render(self):
        """Render current color, brightness, and optional window mask."""
        rgb = self._rgb()
        if self.single_window is None:
            for i in range(LED_COUNT):
                self.np[i] = rgb
            self.write_leds()
            return

        active_pair = WINDOWS[self.single_window - 1][2]
        for i in range(LED_COUNT):
            self.np[i] = rgb if i in active_pair else (0, 0, 0)
        self.write_leds()

    def set_color(self, name):
        """Set solid color (R, G, B, W, or OFF)."""
        key = COLOR_ALIASES.get(str(name).strip().upper())
        if key is None:
            print(f"Unknown color '{name}'. Use R, G, B, W, or OFF.")
            return
        if key == "OFF":
            self.single_window = None
        self.color_name = key
        self._warn_if_high_current()
        self.render()
        scope = (
            f"WIN {self.single_window} ({WINDOWS[self.single_window - 1][0]})"
            if self.single_window is not None
            else "ALL 28 LEDs"
        )
        print(f"Annunciator: {key} @ {self.brightness}/255 [{scope}]")

    def set_brightness(self, val):
        """Set brightness (0..255 or 'NN%') and immediately re-render."""
        parsed = _parse_brightness(val)
        if parsed is None:
            print(f"Invalid brightness '{val}'. Use 0-255 or 0%-100%.")
            return
        self.brightness = parsed
        if self.brightness > 100:
            print(
                f"Note: brightness {self.brightness}/255; full white on all 28 WS2813B-V5 LEDs "
                "at 255 draws ~1.34 A (use an external 5V supply for high brightness)."
            )
        self.render()
        print(
            f"Annunciator brightness: {self.brightness}/255 "
            f"({(self.brightness * 100) // 255}%) [color={self.color_name}]"
        )

    def set_window(self, num):
        """Isolate a single annunciator window (1..14)."""
        try:
            idx = int(str(num).strip())
        except ValueError:
            print(f"Invalid window '{num}'. Use 1..14 (type LIST to see windows).")
            return
        if not 1 <= idx <= len(WINDOWS):
            print(f"Window {idx} out of range. Use 1..{len(WINDOWS)}.")
            return
        self.single_window = idx
        if self.color_name == "OFF":
            self.color_name = "W"
        label, refs, led_pair = WINDOWS[idx - 1]
        self.render()
        print(
            f"Annunciator WIN {idx:2d}: '{label}' ({refs}, LEDs {led_pair[0]}&{led_pair[1]}) "
            f"= {self.color_name} @ {self.brightness}/255"
        )

    def show_all_windows(self):
        """Exit single-window isolation and light all 28 LEDs."""
        self.single_window = None
        if self.color_name == "OFF":
            self.color_name = "W"
        self._warn_if_high_current()
        self.render()
        print(f"Annunciator: ALL 28 LEDs = {self.color_name} @ {self.brightness}/255")

    def cycle(self):
        """Cycle R -> G -> B -> W -> OFF (0.8 s each) at current brightness."""
        print(f"Annunciator color cycle @ {self.brightness}/255...")
        self.single_window = None
        for name in ("R", "G", "B", "W", "OFF"):
            self.set_color(name)
            time.sleep_ms(800)

    def chase(self):
        """Step through all 14 annunciator windows (2 LEDs per window)."""
        prev_color = self.color_name
        prev_win = self.single_window
        chase_color = "W" if prev_color == "OFF" else prev_color
        rgb = _scale_rgb(COLOR_MAP[chase_color], self.brightness or 50)
        print(f"Annunciator window chase ({chase_color}):")
        for idx, (label, refs, pair) in enumerate(WINDOWS, 1):
            for i in range(LED_COUNT):
                self.np[i] = rgb if i in pair else (0, 0, 0)
            self.write_leds()
            print(f"  {idx:2d}. {label:<11} ({refs}, LEDs {pair[0]:2d}&{pair[1]:2d})")
            time.sleep_ms(250)
        self.color_name = prev_color
        self.single_window = prev_win
        self.render()

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
        elif verb == "LIST":
            print_windows()
        elif verb == "ALL":
            self.show_all_windows()
        elif verb == "WIN" and arg:
            self.set_window(arg)
        elif verb == "CYCLE":
            self.cycle()
        elif verb == "CHASE":
            self.chase()
        elif verb in COLOR_ALIASES:
            self.set_color(verb)
        elif verb in ("BRI", "BRIGHT", "BRIGHTNESS") and arg:
            self.set_brightness(arg)
        elif _parse_brightness(upper) is not None:
            self.set_brightness(upper)
        else:
            print(f"Unknown annunciator command '{raw}'. Type HELP for options.")
        return True

    def off(self):
        """Turn off all 28 annunciator LEDs immediately."""
        self.color_name = "OFF"
        self.single_window = None
        for i in range(LED_COUNT):
            self.np[i] = (0, 0, 0)
        self.write_leds()


def print_windows():
    """Print the 14 annunciator windows and their LED designators."""
    for idx, (label, refs, pair) in enumerate(WINDOWS, 1):
        print(f"  {idx:2d}. {label:<11} {refs:<7} (LEDs {pair[0]:2d},{pair[1]:2d})")


def print_help():
    """Print available Thonny shell commands for annunciator testing."""
    print(
        "Annunciator commands: R | G | B | W | OFF | BRI <0-255 or %> | "
        "WIN <1-14> | ALL | LIST | CYCLE | CHASE | HELP | Q"
    )


def run():
    """Start interactive Thonny shell test loop for the Annunciator board."""
    tester = AnnunciatorTester()
    print(f"Annunciator tester ready on GP{LED_PIN} ({LED_COUNT} LEDs, brightness={tester.brightness}/255).")
    print_help()
    try:
        while True:
            try:
                line = input("ANN> ")
            except EOFError:
                break
            if not tester.handle_command(line):
                break
    except KeyboardInterrupt:
        print("\nAnnunciator test interrupted.")
    finally:
        tester.off()
        print("Annunciator LEDs OFF.")


if __name__ == "__main__":
    run()
