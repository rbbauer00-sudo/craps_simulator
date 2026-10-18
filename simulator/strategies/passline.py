from engine import (
    Game, 
    Player,
    Wager, 
    WagerType, 
    defs, 
)

from ..strategy import Strategy

class PassLineStrategy(Strategy):
    def __init__(
        self,
        player: Player,
        amount: int = 25,
    ) -> None:
        
        self.player = player
        self.amount = amount

    def before_roll(self, game: Game) -> None:
        if game.point is not None:
            return

        existing = game.get_wager(
            self.player,
            WagerType.PASS_LINE,
        )

        if existing is not None:
            return

        wager = Wager(
            definition=defs.PASS_LINE,
            player=self.player,
            game=game,
            value=self.amount,
        )

        if self.player.bankroll >= self.amount:
            game.place_wager(wager)