from engine import Game
from .strategy import Strategy

class Simulator:
    def __init__(
        self,
        game: Game, 
        strategy: Strategy | None = None,
    )-> None:
        
        self.game = game
        self.strategy = strategy
        self.roll_count = 0

    def step(self):
        if self.strategy:
            self.strategy.before_roll(self.game)
        
        results = self.game.roll()
        self.roll_count += 1

        if self.strategy:
            self.strategy.after_roll(self.game, results)
            
        return results

    def run(self, num_rolls: int) -> None:
        for _ in range(num_rolls):
            self.step()
