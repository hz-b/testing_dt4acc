# python
from p4p.client.thread import Context
import matplotlib.pyplot as plt
import numpy as np
import threading
import getpass
import argparse
import logging
import sys
from typing import Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

class MonitorPlot:
    def __init__(self, prefix: str, update_interval: float = 0.1, window: int = 200) -> None:
        self.prefix = prefix
        self.pv_x = f"{prefix}:beam:orbit:x"
        self.pv_y = f"{prefix}:beam:orbit:y"
        self.update_interval = update_interval

        # fixed window size for the "moving" plot
        self.window = window
        self._x_axis = np.arange(self.window)

        self._lock = threading.Lock()
        # circular buffers for display
        self._buf_x = np.full(self.window, np.nan, dtype=float)
        self._buf_y = np.full(self.window, np.nan, dtype=float)

        self._ctx = Context("pva")
        self._sub_x = None
        self._sub_y = None
        self._stopped = False

        # Matplotlib objects
        plt.ion()
        self._fig, self._ax = plt.subplots()
        (self._line_x,) = self._ax.plot(self._x_axis, self._buf_x, label="x plane", lw=1.5)
        (self._line_y,) = self._ax.plot(self._x_axis, self._buf_y, label="y plane", lw=1.5)
        self._ax.set_title(f"{self.prefix}:beam:orbit (x & y live)")
        self._ax.set_xlabel("Index")
        self._ax.set_ylabel("Value")
        self._ax.legend()
        self._ax.grid(True)
        # keep x limits fixed so the waveform will appear to move
        self._ax.set_xlim(0, self.window - 1)
        self._fig.canvas.mpl_connect("close_event", self._on_close)

    def _to_array(self, value: Any) -> np.ndarray:
        try:
            if isinstance(value, dict) and "value" in value:
                v = value["value"]
            elif hasattr(value, "value"):
                v = getattr(value, "value")
            else:
                v = value
            arr = np.asarray(v, dtype=float)
            return np.atleast_1d(arr)
        except Exception:
            return np.atleast_1d(np.array(value, dtype=float))

    def _append_to_buffer(self, buf: np.ndarray, values: np.ndarray) -> np.ndarray:
        # If incoming chunk larger than window, keep only last window elements
        if values.size >= buf.size:
            return values[-buf.size :].astype(float)
        # roll left by n and place new values at the end
        n = values.size
        buf = np.roll(buf, -n)
        buf[-n:] = values
        return buf

    def _update_y_limits(self) -> None:
        # compute min/max ignoring NaNs and add small margin
        combined = np.concatenate([self._buf_x[~np.isnan(self._buf_x)], self._buf_y[~np.isnan(self._buf_y)]])
        if combined.size == 0:
            return
        vmin, vmax = combined.min(), combined.max()
        if np.isfinite(vmin) and np.isfinite(vmax):
            margin = max(1e-6, 0.05 * (vmax - vmin) if vmax != vmin else 0.1)
            self._ax.set_ylim(vmin - margin, vmax + margin)

    def _on_update_x(self, value: Any) -> None:
        with self._lock:
            arr = self._to_array(value)
            self._buf_x = self._append_to_buffer(self._buf_x, arr)

    def _on_update_y(self, value: Any) -> None:
        with self._lock:
            arr = self._to_array(value)
            self._buf_y = self._append_to_buffer(self._buf_y, arr)

    def _on_close(self, event: Any) -> None:
        logging.info("Figure closed, stopping monitor.")
        self._stopped = True

    def start(self) -> None:
        logging.info("Monitoring:\n  %s\n  %s\n(close the window to stop)", self.pv_x, self.pv_y)
        self._sub_x = self._ctx.monitor(self.pv_x, self._on_update_x)
        self._sub_y = self._ctx.monitor(self.pv_y, self._on_update_y)

        try:
            while not self._stopped and plt.fignum_exists(self._fig.number):
                updated = False
                with self._lock:
                    # update line data (x-axis fixed)
                    self._line_x.set_ydata(self._buf_x)
                    self._line_y.set_ydata(self._buf_y)
                    updated = True

                    if updated:
                        # update y-limits only (keeps x ticks stable so waveform moves)
                        self._update_y_limits()

                plt.pause(self.update_interval)
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt, stopping.")
        finally:
            if self._sub_x is not None:
                try:
                    self._sub_x.close()
                except Exception:
                    pass
            if self._sub_y is not None:
                try:
                    self._sub_y.close()
                except Exception:
                    pass
            try:
                self._ctx.close()
            except Exception:
                pass
            logging.info("Stopped monitoring.")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Live plot of beam orbit (x & y).")
    parser.add_argument("--prefix", "-p", default=getpass.getuser(), help="PV prefix (default: current user)")
    parser.add_argument("--interval", "-i", type=float, default=0.1, help="Update interval in seconds")
    parser.add_argument("--window", "-w", type=int, default=200, help="Number of points in moving window")
    args = parser.parse_args(argv)

    monitor = MonitorPlot(prefix=args.prefix, update_interval=args.interval, window=args.window)
    monitor.start()


if __name__ == "__main__":
    main(sys.argv[1:])