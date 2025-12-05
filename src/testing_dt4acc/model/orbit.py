"""Represent orbit results in a more digestable manner
"""
from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class OrbitPosition:
    """Orbit at current position

    Todo:
        still using swapped dp, ct
    """

    #: horizontal position
    x: float
    #: horizontal "angle"
    xp: float
    #: vertical position
    z: float
    #: vertical angle
    zp: float
    dp: float
    ct: float

    def as_sequence(self):
        return self.x, self.xp, self.z, self.zp, self.dp, self.ct

    def is_valid(self):
        return bool(np.isfinite(self.as_sequence()).all())


@dataclass
class NamedOrbitPosition:
    name: str
    pos: OrbitPosition


@dataclass
class OrbitResult:
    # start point where it started
    ref: NamedOrbitPosition
    orbit: Sequence[NamedOrbitPosition]
