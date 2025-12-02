# README.md
Run the Bessy II Digital Twin 
```bash 
apptainer run oras://registry.hzdr.de/digital-twins-for-accelerators/containers/pyat-softioc-digital-twin:v0-1-2-bessy.2475331
```

## Overview
This repository contains three scripts to interact with the digital twin via `p4p` and to visualize beam data:

- `scripts/move_steerer.py` — perform a small ±0.01 move sequence on a steerer PV.
- `scripts/plot_orbit.py` — live moving-window plot of two PVs: `:beam:orbit:x` and `:beam:orbit:y`.
- `scripts/plot_twiss.py` — live plot of twiss beta arrays: `:beam:twiss:x:beta` and `:beam:twiss:y:beta`.

Each script by default uses the current OS user as the PV prefix (via `getpass.getuser()`) (similar in the twin); a `--prefix` or `--pv` argument allows overriding.

## Install
Create a virtual environment and install requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


# uses default PV <current_user>:HS4P1D1R:set
python3 scripts/move_steerer.py

# or specify PV explicitly
python3 scripts/move_steerer.py 



# uses default prefix = current user
python3 scripts/plot_orbit.py

# customize prefix, update interval, and window size
python3 scripts/plot_orbit.py 


python3 scripts/plot_twiss.py

# with explicit prefix and interval
python3 scripts/plot_twiss.py 
```
