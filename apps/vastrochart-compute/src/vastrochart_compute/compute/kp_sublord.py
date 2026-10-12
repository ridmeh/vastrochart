"""K.P. (Krishnamurti Paddhati) sub-lord and sub-sub-lord.

Per docs/01-vision.md this precision is the stated competitive moat, so
boundary correctness matters more here than almost anywhere else in the
compute engine.

Rules (docs/02-domain-knowledge.md, standard K.P. practice - see the
"Krishnamurti Padhdhati" readers cited there):
- Each nakshatra (13 deg 20') divides into 9 sub-arcs, proportioned by the
  Vimshottari dasha years (sum 120).
- The sub sequence starts from the NAKSHATRA's own lord (not a fixed
  Ketu-start) and proceeds in the fixed Vimshottari cyclic order.
- Sub-sub repeats this one level deeper, starting from that SUB's own lord
  (not the nakshatra lord again) - each level restarts the 9-fold cycle from
  its own immediately-preceding lord.

Segment math is shared with compute/dasha.py via compute/vimshottari.py -
same proportioning rule, one source of truth.

Not yet cross-verified against golden data: the AstroSage exports used for
tests/golden/private_*.json don't display a sub-lord column, so this module
is currently self-consistency-tested only (see tests/unit/test_kp_sublord.py)
- flag this if/when a K.P.-specific reference becomes available.
"""

from dataclasses import dataclass
from fractions import Fraction

from vastrochart_compute.compute.constants import NAKSHATRAS
from vastrochart_compute.compute.vimshottari import locate_segment, proportion_segments

NAKSHATRA_ARC_FRACTION = Fraction(40, 3)  # 13 deg 20', exact


@dataclass(frozen=True)
class SubLordResult:
    nakshatra_lord: str
    sub_lord: str
    sub_sub_lord: str


def compute_kp_sub_lords(sidereal_longitude: float) -> SubLordResult:
    longitude = Fraction(sidereal_longitude % 360)
    nakshatra_index = int(longitude // NAKSHATRA_ARC_FRACTION) % 27
    nakshatra_lord = NAKSHATRAS[nakshatra_index][1]
    offset_in_nakshatra = longitude - nakshatra_index * NAKSHATRA_ARC_FRACTION

    sub_lord, sub_start, sub_end = locate_segment(
        offset_in_nakshatra, proportion_segments(nakshatra_lord, NAKSHATRA_ARC_FRACTION)
    )
    offset_in_sub = offset_in_nakshatra - sub_start

    sub_sub_lord, _, _ = locate_segment(
        offset_in_sub, proportion_segments(sub_lord, sub_end - sub_start)
    )

    return SubLordResult(
        nakshatra_lord=nakshatra_lord, sub_lord=sub_lord, sub_sub_lord=sub_sub_lord
    )
