import glob
import os
import struct

class DskyLedDriver:
    REPORT_ID = 4
    CMD_SET_BRIGHTNESS = 0x01
    CMD_SET_RANGE      = 0x02
    CMD_SHOW           = 0x03

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

    def set_led_range(self, offset: int, count: int, color: tuple[int, int, int], show: bool = True):
        """Sets `count` LEDs starting at `offset` to a single `(r, g, b)` color."""
        r, g, b = color
        payload = struct.pack("<BBBBBBBx", self.CMD_SET_RANGE, offset, count, r, g, b, int(show))
        self._send(payload)

    def show(self):
        """Flushes staged LED updates to the physical strip."""
        self._send(struct.pack("<B7x", self.CMD_SHOW))

    def clear(self, num_leds: int = 28):
        """Turns off all LEDs."""
        self.set_led_range(0, num_leds, (0, 0, 0), show=True)

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

if __name__ == "__main__":
    leds = DskyLedDriver()
    leds.set_brightness(0.25, show=False)
    leds.set_led_range(offset=0, count=5, color=(0, 255, 0), show=True)
    leds.close()
