from dataclasses import dataclass
from typing import Sequence


@dataclass
class PlaneLimits:
    min: float
    max: float


@dataclass
class ApertureLimits:
    x: PlaneLimits
    z: PlaneLimits

    @classmethod
    def from_aperture_data(cls, data: Sequence[float]):
        data = [float(v) for v in data]
        x_min, x_max, z_min, z_max = data
        return cls(
            x=PlaneLimits(min=x_min, max=x_max), z=PlaneLimits(min=z_min, max=z_max)
        )

    def get_aperture_data(self) -> Sequence[float]:
        return self.x.min, self.x.max, self.z.min, self.z.max
