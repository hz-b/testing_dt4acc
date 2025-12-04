from typing import Sequence

from ..model.survey import NamedSPosition


def compute_s_pos(lattice) -> Sequence[NamedSPosition]:
    return [
        NamedSPosition(name=elem.FamName, s=s)
        for elem, s in zip(lattice, lattice.get_s_pos())
    ]
