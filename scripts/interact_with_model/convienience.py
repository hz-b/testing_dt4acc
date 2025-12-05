import pprint

import numpy as np
import matplotlib.pyplot as plt
from lat2db.model.accelerator import Accelerator
import at

from testing_dt4acc.bl.insert_scraper import insert_scraper
from testing_dt4acc.bl.lookup_table import build_simple_lut
from testing_dt4acc.bl.orbit import find_orbit
from testing_dt4acc.bl.track import track, plot_track
from testing_dt4acc.bl.survey import compute_s_pos
from testing_dt4acc.model.aperture_limits import ApertureLimits
from testing_dt4acc.model.survey import NamedSPosition


mls_lattice = Accelerator(file_name="mls_lattice_json.json", from_json=True).ring
mls_length_orig = mls_lattice.cell_length


mls_lattice_with_collimator = insert_scraper(mls_lattice, 91)

# Here I can access the elements by name
# **NB** this lut has to be rebuilt anytime the lattice is changed!
lut = build_simple_lut(mls_lattice_with_collimator)
print(lut["test_scraper"])

# Lattice length should be close to 240.0 m
print(f"MLS lattice length change:  {mls_length_orig - mls_lattice.cell_length}")
print(f"MLS lattice length change:  {mls_length_orig - mls_lattice.cell_length}")


scraper = lut["test_scraper"].element
# I placed them there ... So I can also access them in this manner
aperature_entrance = mls_lattice_with_collimator[lut["test_scraper"].index - 1]
aperature_exit = mls_lattice_with_collimator[lut["test_scraper"].index + 1]
ap_lims = ApertureLimits.from_aperture_data(scraper.RApertures)
pprint.pprint(ap_lims)

res = find_orbit(mls_lattice_with_collimator)

pprint.pprint(res.ref)

# now redefine limits
ap_lims.z.max = -10e-3
ap_lims.z.min = -25e-3
scraper.RApertures = ap_lims.get_aperture_data()

scraper_in = find_orbit(mls_lattice_with_collimator)
pprint.pprint(scraper_in.ref)

track_along_ring, track_param, track_data = track(
    mls_lattice_with_collimator, res.ref.pos
)
track_interest = track_along_ring[190:215]
bpms = [elem for elem in track_interest if elem.name[:3] == "BPM"]
pprint.pprint(track_interest)
pprint.pprint([(info.name, info.pos.is_valid()) for info in track_interest])

# Prepare orbit plot and plot positions to it
s_pos = compute_s_pos(mls_lattice_with_collimator)
(s_pos_start,) = [item for item in s_pos if item.name == aperature_entrance.FamName]
(s_pos_end,) = [item for item in s_pos if item.name == aperature_exit.FamName]

ap_limits = ApertureLimits.from_aperture_data(scraper.RApertures)

# add the scraper


ax_lines, _, __ = at.plot_trajectory(
    mls_lattice_with_collimator,
    np.array(res.ref.pos.as_sequence()),
)
x_line, y_line = ax_lines.get_lines()

# The correctors that can be changed
vs_us1 = lut["S2M1K3RP"]
vs_us2 = lut["S3M1K3RP"]
vs_ds1 = lut["S3M2K3RP"]
vs_ds2 = lut["S2M2K3RP"]


def get_spos(name: str) -> NamedSPosition:
    (t_pos,) = [item for item in s_pos if item.name == name]
    return t_pos


vs_us1_s, vs_us2_s, vs_ds1_s, vs_ds2_s = [
    get_spos(item.element.FamName) for item in (vs_ds1, vs_ds2, vs_us1, vs_us2)
]


# Plot the collimator position ... x
# ax_lines.plot(
#     [s_pos_start.s, s_pos_start.s, s_pos_end.s, s_pos_end.s, s_pos_start.s],
#     [ap_limits.x.min, ap_limits.x.max, ap_limits.x.max, ap_limits.x.min, ap_limits.x.min],
#     ':',
#     linewidth=2.0,
#     color=x_line.get_color(),
#     label="collimator_x"
# )
# Plot the collimator position ... z
ax_lines.plot(
    [s_pos_start.s, s_pos_start.s, s_pos_end.s, s_pos_end.s, s_pos_start.s],
    [
        ap_limits.z.min,
        ap_limits.z.max,
        ap_limits.z.max,
        ap_limits.z.min,
        ap_limits.z.min,
    ],
    "-",
    linewidth=2.0,
    color=y_line.get_color(),
    label="collimator_y",
)
for elem_spos in vs_us1_s, vs_us2_s, vs_ds1_s, vs_ds2_s:
    ax_lines.plot(
        [elem_spos.s, elem_spos.s],
        [-10e-3, 10e-3],
        "k-",
        linewidth=2,
        label=f"vs: {elem_spos.name}",
    )
    ax_lines.text(
        elem_spos.s,
        10e-3,
        f"vs: {elem_spos.name}",
        rotation=45,
        horizontalalignment="left",
        verticalalignment="bottom",
    )


def apply_corrections(angles):
    """

    How to try to find it:
        1. angle: get off the axis and aim to the open whole
        2. angle: try to get the beam "some how" straight afterwards
        3. angle: get beam to the center of the last steerer
        4. angle: steer it arond the ring
    """
    for elem, angle in zip([vs_us1, vs_us2, vs_ds1, vs_ds2], angles):
        elem.element.KickAngle[1] = angle


def plot_track_enc(*, start_pos=res.ref.pos, **kws):
    plot_track(
        lattice=mls_lattice_with_collimator,
        start_pos=start_pos,
        s_pos=s_pos,
        axis=ax_lines,
        **kws,
    )


# for a position of -5 .. - 25 mm
# first steps made by hand
apply_corrections(np.array([-10, 3.75, 3.5, -9.75]) * 1e-3)
# returned ... looking precisly what should be there
# watch .. out the second angle needs to get it in straight
apply_corrections(np.array([-10, 3.51, 3.51, -10]) * 1e-3)
plot_track_enc()

new_orbit = find_orbit(mls_lattice_with_collimator)
try:
    plot_track_enc(start_pos=new_orbit.ref.pos, linestyle="dashed")
except AssertionError as ae:
    print(f"Failed to get track after correction: {ae}")

# ax_lines.set_xlim(35, 55)
ax_lines.set_ylim(-50e-3, 50e-3)
# plt.show()
# pprint.pprint(  )
# pprint.pprint( find_orbit(bessyii_lattice_with_collimator) )
