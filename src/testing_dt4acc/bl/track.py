from typing import Sequence, Dict, Union, Tuple

import numpy as np
import at

from ..model.orbit import OrbitPosition, OrbitResult, NamedOrbitPosition


def track(
    lattice, start_pos: OrbitPosition
) -> Tuple[
    Sequence[NamedOrbitPosition],
    Dict[str, Union[int, Sequence[float], Sequence[int]]],
    Dict[str, Union[int, float, Sequence[float]]],
]:
    t_track, track_param, track_data = at.lattice_track(
        lattice, np.array(start_pos.as_sequence()), refpts=at.All
    )

    n_dim, n_particles, n_elm, n_turns = t_track.shape
    assert n_particles == 1
    assert n_turns == 1
    assert n_dim == 6
    assert n_elm == len(lattice) + 1

    t_track = t_track[:, 0, :, 0]

    track = [
        NamedOrbitPosition(
            name=elem.FamName, pos=OrbitPosition(*[float(v) for v in pos])
        )
        for elem, pos in zip(lattice, t_track.transpose())
    ]
    return track, track_param, track_data


def plot_track(*, lattice, start_pos, axis, s_pos, **kws):
    track_along_ring, track_param, track_data = track(lattice, start_pos)

    new_orbit = np.array(
        [
            (s.s, item.pos.z)
            for s, item in zip(s_pos, track_along_ring)
            if item.pos.is_valid()
        ]
    )
    if len(new_orbit) == 0:
        raise AssertionError("Did not find any track at all!")
    kws.setdefault("linestyle", "dashdot")
    (line,) = axis.plot(
        new_orbit[:, 0],
        new_orbit[:, 1],
        **kws,
    )

    bpm_orbit = np.array(
        [
            (s.s, item.pos.z)
            for s, item in zip(s_pos, track_along_ring)
            if item.pos.is_valid() and item.name[:3] == "BPM"
        ]
    )

    kws = kws.copy()
    if "color" in kws.keys():
        kws.pop("color")

    axis.plot(
        bpm_orbit[:, 0],
        bpm_orbit[:, 1],
        "o",
        color=line.get_color(),
    )
