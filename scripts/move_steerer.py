# python
import time
import logging
import argparse
import getpass
from typing import Any
from p4p.client.thread import Context

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")


def _extract_number(value: Any) -> float:
    # handle common p4p return shapes
    if isinstance(value, dict) and "value" in value:
        v = value["value"]
    elif hasattr(value, "value"):
        v = getattr(value, "value")
    else:
        v = value

    # If it's an array-like, take first element
    try:
        # simple numeric
        return float(v)
    except Exception:
        try:
            # sequence/array
            return float(v[0])
        except Exception as exc:
            raise ValueError("Couldn't extract numeric value from PV read") from exc


def perform_sequence(ctx: Context, pv: str, delay: float) -> None:
    logging.info("Reading current value of %s", pv)
    r = ctx.get(pv)
    try:
        current = _extract_number(r)
    except Exception as e:
        logging.error("Failed to read PV value: %s", e)
        return

    logging.info("Current value: %s", current)

    # Build sequence: +0.01, original, -0.01, original, +0.01
    step = 0.01
    seq = [current + step, current, current - step, current, current + step]

    for i, val in enumerate(seq, start=1):
        try:
            logging.info("Setting %s -> %s (step %d/%d)", pv, val, i, len(seq))
            ctx.put(pv, val)
        except Exception as e:
            logging.error("Failed to write value %s to %s: %s", val, pv, e)
            break
        time.sleep(delay)

    logging.info("Sequence completed.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Perform ±0.01 change sequence on a PV using p4p")
    # Use current user as prefix for the default PV
    pv_default = f"{getpass.getuser()}:HS4P1D1R:set"
    parser.add_argument("--pv", "-p", default=pv_default, help="PV name (default: <user>:HS4P1D1R:set)")
    parser.add_argument("--delay", "-d", type=float, default=0.5, help="Delay in seconds between writes")
    args = parser.parse_args(argv)

    ctx = Context("pva")
    try:
        perform_sequence(ctx, args.pv, args.delay)
    finally:
        try:
            ctx.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()