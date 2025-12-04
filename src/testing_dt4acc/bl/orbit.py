from ..model.orbit import OrbitResult, NamedOrbitPosition, OrbitPosition
import at


def find_orbit(lattice) -> OrbitResult:
    """shallow wrapper on
    """
    orbit_at_start, orbit_at_elements = lattice.find_orbit(at.All)

    assert len(orbit_at_elements) == len(lattice) + 1, "Did not get full orbit"
    return OrbitResult(
        ref=NamedOrbitPosition(name="ref_point", pos=OrbitPosition(*[float(p) for p in orbit_at_start])),
        orbit=[NamedOrbitPosition(name=elem.FamName, pos=OrbitPosition(*[float(p) for p in t_pos]))
               for elem, t_pos in zip(lattice, orbit_at_elements)
               ]
    )