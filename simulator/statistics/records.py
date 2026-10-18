from dataclasses import dataclass
from engine import PlayerEquity, WagerType, Resolution


@dataclass(frozen=True)
class PlayerSnapshot:
    player_index: int
    name: str
    equity: PlayerEquity


@dataclass(frozen=True)
class WagerOutcome:
    player_id: int
    wager_type: WagerType
    value: int
    target: int | tuple[int, int] | None
    resolution: Resolution
    profit: int
    move_to: int | None


class RollRecord:...
 

class WagerSnapshot:...