from enum import Enum, auto

class RollPhase(Enum):
    READY = auto()
    DICE_ROLLING = auto()
    WAGERS_RESOLVING = auto()
    PUCK_MOVING = auto()
    DICE_RETURNING = auto()
