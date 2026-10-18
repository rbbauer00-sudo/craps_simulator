from engine import Game
from .strategy import Strategy
from .statistics import Statistics

class Simulator:
    def __init__(
        self,
        game: Game, 
        strategy: Strategy | None = None,
    )-> None:
        
        self.game = game
        self.strategy = strategy
        self.statistics = Statistics()

    @property
    def roll_count(self) -> int:
        return self.statistics.roll_count

    def step(self):
        if self.strategy:
            self.strategy.before_roll(self.game)
        
        result = self.game.roll()
        self.statistics.record_roll(result)

        if self.strategy:
            self.strategy.after_roll(self.game, result)
            
        return result

    def run(self, num_rolls: int) -> None:
        for _ in range(num_rolls):
            self.step()
