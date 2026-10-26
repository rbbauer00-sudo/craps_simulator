from dataclasses import dataclass, field
from typing import Any


@dataclass
class StrategyContext:
    game: Any
    player: Any
    roll_result: Any = None

    data: dict = field(default_factory=dict)

    @property
    def bankroll(self) -> int:
        return self.player.bankroll

    @property
    def point(self) -> int | None:
        return self.game.point