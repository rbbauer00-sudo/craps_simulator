from dataclasses import dataclass
from enum import Enum, auto


class AnimationMode(Enum):
    FULL = auto()
    SIMULTANEOUS = auto()
    MINIMAL = auto()
    INSTANT = auto()


@dataclass
class AnimationSettings:
    mode: AnimationMode = AnimationMode.FULL
    speed: float = 1.0