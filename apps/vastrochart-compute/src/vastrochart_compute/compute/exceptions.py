"""Domain exceptions raised by compute/ - translated to API error codes at
the route layer (apps/vastrochart-compute/src/vastrochart_compute/routes/).
"""


class EphemerisRangeError(Exception):
    """Raised when a date is beyond what pyswisseph can compute at all
    (not merely beyond our loaded high-precision files - Moshier's own
    empirically-verified range, roughly -3001-02-03 to 3003-04-29, is the
    real limit). Maps to the DATE_OUT_OF_EPHEMERIS_RANGE error code."""
