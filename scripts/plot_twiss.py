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
    def __init__(self, prefix: str, update_interval: float = 0.1) -> None:
        self.prefix = prefix
        self.pv_x = f"{prefix}:beam:twiss:x:beta"
        self.pv_y = f"{prefix}:beam:twiss:y:beta"
        self.update_interval = update_interval

        self._lock = threading.Lock()
        self._latest_x: Optional[np.ndarray] = None
        self._latest_y: Optional[np.ndarray] = None

        self._ctx = Context("pva")
        self._sub_x = None
        self._sub_y = None
        self._stopped = False

        # Matplotlib objects
        plt.ion()
        self._fig, self._ax = plt.subplots()
        (self._line_x,) = self._ax.plot([], [], label="x plane", lw=1.5)
        (self._line_y,) = self._ax.plot([], [], label="y plane", lw=1.5)
        self._ax.set_title(f"{self.prefix}:beam:twiss:beta (x & y live)")
        self._ax.set_xlabel("Index")
        self._ax.set_ylabel(r"$\beta_{x, y}$")
        self._ax.legend()
        self._ax.grid(True)
        self._fig.canvas.mpl_connect("close_event", self._on_close)

    def _to_array(self, value: Any) -> np.ndarray:
        # Handle a few common p4p structures, scalars, and sequences
        try:
            # value may be a mapping with "value" key
            if isinstance(value, dict) and "value" in value:
                v = value["value"]
            # p4p Value sometimes exposes .value attribute
            elif hasattr(value, "value"):
                v = getattr(value, "value")
            else:
                v = value
            arr = np.asarray(v, dtype=float)
            return np.atleast_1d(arr)
        except Exception:
            # Fallback: try direct conversion of the whole object
            return np.atleast_1d(np.array(value, dtype=float))

    def _on_update_x(self, value: Any) -> None:
        with self._lock:
            self._latest_x = self._to_array(value)

    def _on_update_y(self, value: Any) -> None:
        with self._lock:
            self._latest_y = self._to_array(value)

    def _on_close(self, event: Any) -> None:
        logging.info("Figure closed, stopping monitor.")
        self._stopped = True

    def start(self) -> None:
        logging.info("Monitoring:\n  %s\n  %s\n(close the window to stop)", self.pv_x, self.pv_y)
        # Subscribe
        self._sub_x = self._ctx.monitor(self.pv_x, self._on_update_x)
        self._sub_y = self._ctx.monitor(self.pv_y, self._on_update_y)

        try:
            while not self._stopped and plt.fignum_exists(self._fig.number):
                updated = False
                with self._lock:
                    if self._latest_x is not None:
                        x_axis = np.arange(len(self._latest_x))
                        self._line_x.set_data(x_axis, self._latest_x)
                        updated = True
                    if self._latest_y is not None:
                        y_axis = np.arange(len(self._latest_y))
                        self._line_y.set_data(y_axis, self._latest_y)
                        updated = True

                    if updated:
                        self._ax.relim()
                        self._ax.autoscale_view()

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
    parser = argparse.ArgumentParser(description="Live plot of twiss beta (x & y).")
    parser.add_argument("--prefix", "-p", default=getpass.getuser(), help="PV prefix (default: current user)")
    parser.add_argument("--interval", "-i", type=float, default=0.1, help="Update interval in seconds")
    args = parser.parse_args(argv)

    monitor = MonitorPlot(prefix=args.prefix, update_interval=args.interval)
    monitor.start()


if __name__ == "__main__":
    main(sys.argv[1:])