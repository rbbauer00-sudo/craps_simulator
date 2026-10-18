from abc import ABC
from engine import Game, WagerResult, GameRollResult

class Strategy(ABC):
    def before_roll(
        self, 
        game: Game,
    ) -> None:...

    def after_roll(
        self,
        game: Game,
        results: list[WagerResult]
    ) -> None:...
        

