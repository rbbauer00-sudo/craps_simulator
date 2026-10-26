from dataclasses import dataclass
from enum import Enum, auto


class AnimationMode(Enum):
    FULL = auto()
    SIMULTANEOUS = auto()
    MINIMAL = auto()
    INSTANT = auto()


@dataclass(frozen=True)
class AnimationSettings:
    mode: AnimationMode = AnimationMode.FULL
    speed: float = 1.0

    def __post_init__(self) -> None:
        if not 0 < self.speed < float("inf"):
            raise ValueError(
                "Animation speed must be positive and finite."
            )

    def duration(self, seconds: float) -> float:
        return seconds / self.speed