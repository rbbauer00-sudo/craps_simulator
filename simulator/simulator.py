from engine import Game, GameRollResult
from .strategy import Strategy
from .statistics import SessionRecorder

class Simulator:

    def __init__(
        self,
        game: Game, 
        strategy: Strategy | None = None,
    )-> None:
        
        self.game = game
        self.strategy = strategy

        self.recorder = SessionRecorder()
        self.recorder.capture_opening(self.game)
        self.roll_count: int = 0

    def step(self) -> GameRollResult:

        if self.recorder.is_closed:
            raise RuntimeError(
                "Cannot roll a closed simulation session."
            )
        
        if self.strategy:
            self.strategy.before_roll(self.game)

        players_before = self.recorder.snapshot_players(
            self.game
        )
        wagers_before = self.recorder.snapshot_wagers(
            self.game
        )

        previous_wagers = (
        self.recorder.rolls[-1].wagers_after
        if self.recorder.rolls
        else ()
    )

        wager_changes = self.recorder.reconcile_wagers(
        previous_wagers,
        wagers_before,
    )
        
        result = self.game.roll()

        players_after = self.recorder.snapshot_players(
            self.game
        )
        wagers_after = self.recorder.snapshot_wagers(
            self.game
        )

        self.recorder.record_roll(
            result=result,
            players_before=players_before,
            players_after=players_after,
            wagers_before=wagers_before,
            wagers_after=wagers_after,
            wager_changes_before=wager_changes,
        )

        self.roll_count += 1

        if self.strategy:
            self.strategy.after_roll(self.game, result)
            
        return result

    def run(self, num_rolls: int) -> None:
        for _ in range(num_rolls):
            self.step()

    def close(self) -> None:
        self.recorder.close(self.game)
