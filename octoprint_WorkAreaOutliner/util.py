# GCode Command arguments
X = 'X'
Y = 'Y'
Z = 'Z'

# Shorthand for list indeces
X_ = 0
Y_ = 1
Z_ = 2
MIN_ = 0
MAX_ = 1

class NullBoundException(Exception):
    pass

class FeedrateSource:
    AUTO = "auto"
    CUSTOM = "custom"

class EndMode:
    HOME = "home"
    PARK = "park"
    MODEL = "model"

class ParkPosition:
    MIN = "min"
    MAX = "max"
    MIN_MAX = "min_max"
    MAX_MIN = "max_min"
    CENTER = "center"
    CUSTOM = "custom"