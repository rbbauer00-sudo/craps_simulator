from abc import ABC
from engine import Game, GameRollResult

class Strategy(ABC):
    def before_roll(
        self, 
        game: Game,
    ) -> None:...

    def after_roll(
        self,
        game: Game,
        results: GameRollResult
    ) -> GameRollResult:...
        

