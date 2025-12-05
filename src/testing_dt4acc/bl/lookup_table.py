from collections import defaultdict
from typing import Sequence, Dict

from ..model.lattice_lookup_table import LatticePositionLUTElement


def build_simple_lut(elements: Sequence[object]):
    return produce_simple_lut(build_lut(elements))


def build_lut(elements: Sequence[object]):
    """Group objects together by name"""
    lut = defaultdict(list)
    for idx, elem in enumerate(elements):
        lut[elem.FamName].append(LatticePositionLUTElement(index=idx, element=elem))

    return lut


def produce_simple_lut(
    lut: Dict[str, Sequence[LatticePositionLUTElement]]
) -> Dict[str, LatticePositionLUTElement]:
    assert (
        len([item for _, item in lut.items() if len(item) > 1]) == 0
    ), "Can't build a simple look up table if elements are doubled"

    return {key: elem[0] for key, elem in lut.items()}
