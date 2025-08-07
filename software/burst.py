import time
import math
import adafruit_mlx90393

# ──────────────────────────── Constants ─────────────────────────────
_CMD_AXIS_XY = 0x06          # zyxt nibble: Z=0 Y=1 X=1 T=0 → XY only
_CMD_REG_CONF2 = 0x01        # CONF2 contains BURST bits when using RAM path

# Status‑byte bit masks (datasheet §15)
_STATUS_BURST = 0x80
_STATUS_WOC   = 0x40
_STATUS_SM    = 0x20
_STATUS_ERR   = 0x10
_STATUS_RS    = 0x04
_STATUS_BA    = 0x03  # number of response bytes available / 2 – 1


class FastXY(adafruit_mlx90393.MLX90393):
    """Thin wrapper that enters **XY‑only burst mode** immediately.

    Design rules follow the official Adafruit C++ driver:
      • Use the *command nibble* to select axes (SB | 0x06).
      • Do **not** rely on CONF2 for BURST_SEL – avoids ERR 0x92.
    """

    # ───────────────────────── Constructor ──────────────────────────
    def __init__(self, *args, burst_rate: int = 0, **kwargs):
        super().__init__(*args, **kwargs)
        self._burst_rate = burst_rate & 0x7F  # 7‑bit field, each step = 20 ms
        self._start_burst_xy()

    # ───────────────────────── Internal helpers ─────────────────────
    def _tconv_delay(self) -> float:
        """Return safety‑padded TCONV for *two* axes (ms table → s)."""
        t_ms = adafruit_mlx90393._TCONV_LOOKUP[self._filter][self._osr]
        return (t_ms * 2 / 3) / 1000.0 * 1.1

    def _start_burst_xy(self):
        print("Starting XY burst mode with rate", self._burst_rate)
        """Program CONF2 (BURST_SEL = XY, optional rate) then issue SB (0x10)."""
        conf2 = self.read_reg(_CMD_REG_CONF2)
        print("conf2", hex(conf2))
        # Clear old BURST_SEL[3:0] and BURST_DATA_RATE[10:4]
        conf2 &= 0xF800
        conf2 |= _CMD_AXIS_XY << 6               # set BURST_SEL = 0b0110 (XY)
        conf2 |= (self._burst_rate)    # set optional data‑rate
        print("conf2", hex(conf2), self._status_last)

        self.write_reg(_CMD_REG_CONF2, conf2)
        conf2 = self.read_reg(_CMD_REG_CONF2)
        print("conf2", hex(conf2), self._status_last)

        # Issue SB with nibble 0 so chip uses BURST_SEL from CONF2
        try:
            self._transceive(bytes([adafruit_mlx90393._CMD_SB]))
        except OSError:
            return
        time.sleep(self._tconv_delay())  # wait first conversion  # let first conversion finish

    def _read_xy_packet(self):
        """Perform **RM | XY** (0x46) → returns status + 4 bytes."""
        # try:
        buf = self._transceive(bytes([adafruit_mlx90393._CMD_RM | _CMD_AXIS_XY]), 4)
        # print(buf, self._status_last)
        # except OSError:
        #     self._start_burst_xy()
        #     return None, None

        self._status_last = buf[0]

        # If ERR set, re‑arm burst and abort this sample
        if self._status_last & _STATUS_ERR:
            time.sleep(10e-6)
            # print("YO")
            buf = self._transceive(bytes([adafruit_mlx90393._CMD_RM | _CMD_AXIS_XY]), 4)
            # print(buf, self._status_last)
            self._status_last = buf[0]

            # self._start_burst_xy()
            #return None, None

        # If no bytes available yet, skip sample (BA bits == 0)
        if (self._status_last & _STATUS_BA) == 0:
            return None, None

        mx = self._unpack_axis_data(self._res_x, buf[1:3])
        my = self._unpack_axis_data(self._res_y, buf[3:5])

        # Datasheet: not‑ready axes return 0xFFFF → −1 after unpack
        if mx == -1 and my == -1:
            return None, None
        return mx, my

    # ───────────────────────── Public API ───────────────────────────
    def burst_xy(self):
        """Get latest XY tuple or ``(None, None)`` if not ready."""
        return self._read_xy_packet()