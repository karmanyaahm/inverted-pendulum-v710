import time
import math
import adafruit_mlx90393

_CMD_AXIS_XY = 0x6
_CMD_REG_CONF2 = 0x01

class FastXY(adafruit_mlx90393.MLX90393):
    """Drop-in replacement that adds
    * faster single-shot X & Y reads (`read_xy`)
    * burst-mode streaming (`start_burst`, `burst_xy`, `stop_burst`)
    * polar heading helper (`heading`)
    """
   
    def _rm_xy(self):
        """Low-level `RM` read helper that returns raw (mx,my)."""
        data = self._transceive(bytes([adafruit_mlx90393._CMD_RM | _CMD_AXIS_XY]), 4)
        self._status_last = data[0]
        mx = self._unpack_axis_data(self._res_x, data[1:3])
        my = self._unpack_axis_data(self._res_y, data[3:5])
        return mx, my
  
    def _config_burst_xy(self, rate: int = 0):
        """Write BURST_SEL + BURST_DATA_RATE in volatile RAM.

        *rate* ∈ [0,127] sets TINTERVAL = rate·20 ms. 0 ⇒ continuous. """
        reg = self.read_reg(_CMD_REG_CONF2)
        reg &= ~0x07FF
        reg |= ((rate & 0x7F) << 4) | _CMD_AXIS_XY
        self.write_reg(_CMD_REG_CONF2, reg)

    def start_burst(self, rate: int = 0):
        """Enter burst mode streaming X & Y only.

        Call once; thereafter read samples with :py:meth:`burst_xy`.
        """
        self._config_burst_xy(rate)
        # SB with zyxt = 0 → use BURST_SEL bits we just programmed
        self._transceive(bytes([adafruit_mlx90393._CMD_SB]))

    def burst_xy(self):
        """Return latest (mx,my) while burst mode is running."""
        return self._rm_xy()