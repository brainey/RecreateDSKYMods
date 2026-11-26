import glob
import os
import struct
import time

class DskyLedDriver:
    # TODO make these definitions imported by both this program and the firmware
    REPORT_ID = 4
    CMD_SET_BRIGHTNESS = 0x01
    CMD_SET_RANGE      = 0x02
    CMD_SHOW           = 0x03

    INDICATORS = {
        1: {"label": "UPLINK ACTY", "leds": (0,1), "pins": "D27/D28", "phys_leds": (16, 17)},
        2: {"label": "TEMP",        "leds": (2,3), "pins": "D1/D2",   "phys_leds": (18, 19)},
        3: {"label": "NO ATT",      "leds": (4,5), "pins": "D25/D26", "phys_leds": (14, 15)},
        4: {"label": "GIM LOCK",    "leds": (6,7), "pins": "D3/D4",   "phys_leds": (20, 21)},
        5: {"label": "STBY",        "leds": (8,9), "pins": "D23/D24", "phys_leds": (12, 13)},
        6: {"label": "PROG",        "leds": (10,11), "pins": "D5/D6",   "phys_leds": (22, 23)},
        7: {"label": "KEY REL",     "leds": (12,13), "pins": "D21/D22", "phys_leds": (10, 11)},
        8: {"label": "RSTRT",       "leds": (14,15), "pins": "D7/D8",   "phys_leds": (24, 25)},
        9: {"label": "OPR ERR",     "leds": (16,17), "pins": "D19/D20", "phys_leds": (8, 9)},
        10: {"label": "TRKR",        "leds": (18,19), "pins": "D9/D10",  "phys_leds": (26, 27)},
        11: {"label": "PRIO DISP",   "leds": (20,21), "pins": "D17/D18", "phys_leds": (6, 7)},
        12: {"label": "ALT",         "leds": (22,23), "pins": "D11/D12", "phys_leds": (0, 1)},
        13: {"label": "NO DAP",      "leds": (24,25), "pins": "D15/D16", "phys_leds": (4, 5)},
        14: {"label": "VEL",         "leds": (26,27), "pins": "D13/D14", "phys_leds": (2, 3)},
    }

    LED_ORDER_MAP = [
        0, 1, 2, 3, 4, 5, 6, 7,
        8, 9, 10, 11, 12, 13, 14, 15,
        16, 17, 18, 19, 20, 21, 22, 23,
        24, 25, 26, 27
    ]

    brightness = 0.5

    def __init__(self, vid="2E8A", pid="10B0"):
        self.path = self._find_hidraw_path(vid.upper(), pid.upper())
        if not self.path:
            raise RuntimeError(f"DSKY HID device {vid}:{pid} not found")
        self.fd = os.open(self.path, os.O_WRONLY)

    @staticmethod
    def _find_hidraw_path(vid: str, pid: str) -> str | None:
        for hidraw in glob.glob("/sys/class/hidraw/hidraw*"):
            uevent = os.path.join(hidraw, "device/uevent")
            if os.path.exists(uevent):
                with open(uevent) as f:
                    info = f.read().upper()
                    if f"0000{vid}" in info and f"0000{pid}" in info:
                        return f"/dev/{os.path.basename(hidraw)}"
        return None

    def _send(self, payload: bytes):
        assert len(payload) == 8
        os.write(self.fd, bytes([self.REPORT_ID]) + payload)

    def set_brightness(self, brightness: float, show: bool = True):
        """Sets global strip brightness from 0.0 (off) to 1.0 (full)."""
        level = max(0, min(255, round(brightness * 255)))
        payload = struct.pack("<BBB5x", self.CMD_SET_BRIGHTNESS, level, int(show))
        self._send(payload)
        self.brightness = brightness

    def set_led_range(self, offset: int, count: int, color: tuple[int, int, int], show: bool = True):
        """Sets `count` LEDs starting at `offset` to a single `(r, g, b)` color."""
        r, g, b = color
        payload = struct.pack("<BBBBBBBx", self.CMD_SET_RANGE, offset, count, r, g, b, int(show))
        self._send(payload)

    def show(self):
        """Flushes staged LED updates to the physical strip."""
        self._send(struct.pack("<B7x", self.CMD_SHOW))

    def clear(self, num_leds: int = 28):
        """Turns off display off by setting brightness to zero for all LEDs."""
        self.set_led_range(0, num_leds, (0, 0, 0), show=True)

    def off(self):
        """Turns display off by setting brightness to zero."""
        payload = struct.pack("<BBB5x", self.CMD_SET_BRIGHTNESS, 0, int(True))
        self._send(payload)
        # don't save brightness state

    def on(self):
        """Turns display back on by setting brightness to previous brightness."""
        self.set_brightness(self.brightness, show=True)

    def set_indicator(self, indicator: int, color: tuple[int, int, int], show: bool = True):
        """Sets a specific indicator LED to a given `(r, g, b)` color."""
        r, g, b = color
        # for led in self.INDICATORS[indicator]["leds"]:
        #     self.set_led_range(led, 1, color, show=show)
        first_led = self.INDICATORS[indicator]["leds"][0]
        self.set_led_range(first_led, 2, color, show=show)
        print(f"Setting indicator {indicator} first LED {first_led} to color {color}")
    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

if __name__ == "__main__":
    leds = DskyLedDriver()
    brightness = 0.5
    print(f"Initialized DSKY LED driver ...setting brightness to {brightness}")

    leds.set_brightness(brightness, show=False)
    offset = 0
    count = 28
    color = (0, 160, 0)
    print(f"Setting LED range offset={offset} count={count} color={color}")
    leds.set_led_range(offset=offset, count=count, color=color, show=True)
    time.sleep(2)  # wait for a second to observe the LEDs after setting the range
    leds.off()
    time.sleep(1)  # wait for a second before closing
    leds.on()
    time.sleep(2)  # wait for a second to observe the LEDs after turning on
    leds.clear()  # clear all LEDs before starting indicator loop

    prev_indicator = None
    for indicator in leds.INDICATORS:
        color = (160, 160, 160)
        print(f"Setting indicator {indicator} to color {color} (previous indicator: {prev_indicator})")
        if prev_indicator is not None:
            leds.set_indicator(prev_indicator, (0, 0, 0), show=True)  # turn off previous indicator
        prev_indicator = indicator
        leds.set_indicator(indicator, color, show=True)
        time.sleep(1)  # wait for a second to observe the indicator LEDs

    time.sleep(1)  # wait for a second before clearing LEDs
    leds.clear()  # clear all LEDs before closing

    leds.close()
