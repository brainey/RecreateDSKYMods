"""DSKY v2 Pico 2 W test launcher for simultaneous Keyboard & Annunciator testing.

Upload main.py, test_keypad.py, and test_annunciator.py to the root (/) of the
Raspberry Pi Pico 2 W in Thonny. On boot, main.py blanks both LED chains and
drops to the Thonny REPL so it never blocks Thonny from connecting.

Thonny Shell functions:
  keypad(self_test=True)  - Run interactive keypad + SK6812MINI-E test
  annunciator()           - Run annunciator WS2813 color/brightness/window test
  both()                  - Run both simultaneously (keys + live shell commands)
  off()                   - Turn off all LEDs on both boards
"""

import select
import sys
import time
from machine import Pin
import neopixel

import test_annunciator
import test_keypad


def _blank_chain(pin_num, count, timing):
    """Turn off an addressable LED chain without touching I2C."""
    np = neopixel.NeoPixel(Pin(pin_num, Pin.OUT), count, bpp=3, timing=timing)
    for i in range(count):
        np[i] = (0, 0, 0)
    np.write()


def off():
    """Turn off all LEDs on both Annunciator (GP0) and Keypad (GP7)."""
    _blank_chain(test_annunciator.LED_PIN, test_annunciator.LED_COUNT, test_annunciator.LED_TIMING)
    _blank_chain(test_keypad.LED_PIN, test_keypad.LED_COUNT, test_keypad.LED_TIMING)
    time.sleep_us(350)


def keypad(self_test=True):
    """Run the standalone Keyboard Assembly test."""
    test_keypad.run(run_self_test=self_test)


def annunciator():
    """Run the standalone Annunciator Assembly test."""
    test_annunciator.run()


def _print_both_help():
    print("Simultaneous mode commands:")
    print("  Unprefixed (or A <cmd>): Annunciator -> R | G | B | W | OFF | BRI <0-255|%> | WIN <1-14> | ALL | CHASE | CYCLE | LIST")
    print("  K <cmd>                : Keypad      -> K R | K G | K B | K W | K OFF | K BRI <0-255|%> | K KEY | K RESET | K CHASE")
    print("  ALL <cmd>              : Both boards -> ALL OFF | ALL BRI 50 | ALL R | ALL G | ALL B | ALL W")
    print("  Q / Ctrl+C             : Turn off both boards and exit")


def _dispatch_both(raw_line, ann, kp):
    """Route a shell command in simultaneous mode. Returns False to exit."""
    raw = raw_line.strip()
    if not raw:
        return True
    upper = raw.upper()
    parts = upper.split(None, 1)
    verb = parts[0]
    arg = parts[1] if len(parts) > 1 else ""

    if verb in ("Q", "QUIT", "EXIT"):
        return False
    if verb in ("HELP", "?"):
        _print_both_help()
        return True

    if verb == "A":
        return ann.handle_command(arg) if arg else (print("Usage: A <command>") or True)

    if verb == "K":
        if kp is None:
            print("Keypad not detected on I2C0 (GP4/GP5).")
            return True
        return kp.handle_command(arg) if arg else (print("Usage: K <command>") or True)

    if verb == "ALL" and arg:
        keep = ann.handle_command(arg)
        if kp is not None:
            keep = kp.handle_command(arg) and keep
        return keep

    return ann.handle_command(raw)


def both():
    """Run Keypad key-press testing and Annunciator controls simultaneously."""
    ann = test_annunciator.AnnunciatorTester()
    kp = None
    try:
        candidate = test_keypad.KeypadTester()
        candidate.init_tca8418()
        candidate.set_key_mode(reset=False)
        kp = candidate
    except (RuntimeError, OSError) as exc:
        print(f"Keypad init skipped ({exc}). Running Annunciator only.")

    poll_obj = select.poll()
    poll_obj.register(sys.stdin, select.POLLIN)
    _print_both_help()
    print("Ready: press keypad keys anytime or enter a command below.")

    try:
        while True:
            if kp is not None:
                kp.poll_keys()
            if poll_obj.poll(0):
                line = sys.stdin.readline()
                if not line or not _dispatch_both(line, ann, kp):
                    break
            time.sleep_ms(10)
    except KeyboardInterrupt:
        print("\nSimultaneous test interrupted.")
    finally:
        ann.off()
        if kp is not None:
            kp.off()
        else:
            _blank_chain(test_keypad.LED_PIN, test_keypad.LED_COUNT, test_keypad.LED_TIMING)
            time.sleep_us(350)
        print("Both boards OFF.")


off()
print("DSKY v2 Pico 2 W Test Suite Ready (LEDs blanked).")
print("  keypad()      - Interactive key matrix + SK6812MINI-E LEDs (GP4/5/6/7)")
print("  annunciator() - Annunciator WS2813 color/brightness/windows (GP0)")
print("  both()        - Run both simultaneously | off() - Blank all LEDs")
