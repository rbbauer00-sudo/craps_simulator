from engine import Game, GameRollResult
from .records import (
    PlayerSnapshot,
    WagerSnapshot,
    WagerOutcome,
    RollRecord,
    WagerChange,
    WagerChangeType
)


class SessionRecorder:
    def __init__(self):
        self._rolls: list[RollRecord] = []
        self._opening_players: tuple[PlayerSnapshot, ...] = ()
        self._opening_captured = False

        self._closing_players: tuple[PlayerSnapshot, ...] | None = None
        self._closing_wagers: tuple[WagerSnapshot, ...] | None = None

    @property
    def opening_players(self) -> tuple[PlayerSnapshot, ...]:
        return self._opening_players

    def capture_opening(self, game: Game) -> None:
        if self._opening_captured:
            raise RuntimeError(
                "Session opening has already been captured."
            )

        self._opening_players = self.snapshot_players(game)
        self._opening_captured = True

    @property
    def rolls(self) -> tuple[RollRecord, ...]:
        return tuple(self._rolls)

    @property
    def roll_count(self) -> int:
        return len(self._rolls)

    def clear(self) -> None:
        self._rolls.clear()
        self._opening_players = ()
        self._opening_captured = False
        self._closing_players = None
        self._closing_wagers = None

    @staticmethod
    def snapshot_players(
        game: Game,
    ) -> tuple[PlayerSnapshot, ...]:
        
        return tuple(
            PlayerSnapshot(
                player_id=player.id,
                name=player.name,
                position=position,
                equity=player.get_equity(),
            )
            for position, player in enumerate(game.players)
        )

    @staticmethod
    def snapshot_wagers(
        game: Game,
    ) -> tuple[WagerSnapshot, ...]:
        
        return tuple(
            WagerSnapshot(
                wager_id=wager.id,
                player_id=wager.player.id,
                wager_type=wager.definition.wager_type,
                value=wager.value,
                target=wager.target,
                is_working=wager.is_working,
                is_buy=wager.is_buy,
                collected_vig=wager.collected_vig,
                contract_min=wager.contract_min,
                contract_max=wager.contract_max,
                parent_wager_id=(
                    wager.parent_wager.id
                    if wager.parent_wager is not None
                    else None
                ),
            )
            for wager in game.wagers
        )

    def record_roll(
        self,
        result: GameRollResult,
        players_before: tuple[PlayerSnapshot, ...],
        players_after: tuple[PlayerSnapshot, ...],
        wagers_before: tuple[WagerSnapshot, ...],
        wagers_after: tuple[WagerSnapshot, ...],
        wager_changes_before: tuple[WagerChange, ...],
    ) -> RollRecord:

        if self.is_closed:
            raise RuntimeError(
                "Cannot record rolls after session closure."
            )

        wager_outcomes = tuple(
            WagerOutcome(
                wager_id=wgr.wager.id,
                player_id=wgr.wager.player.id,
                resolution=wgr.resolution,
                profit=wgr.profit,
                move_to=wgr.move_to,
            )
            for wgr in result.wager_results
        )

        record = RollRecord(
            roll_number=self.roll_count + 1,
            dice=(result.roll.d1, result.roll.d2),
            point_before=result.point_before,
            point_after=result.point_after,
            shooter_id=result.shooter_id,
            shooter_roll_count=result.shooter_roll_count,
            seven_out=result.seven_out,
            players_before=players_before,
            players_after=players_after,
            wagers_before=wagers_before,
            wagers_after=wagers_after,
            wager_changes_before=wager_changes_before,
            wager_outcomes=wager_outcomes,
        )

        self._rolls.append(record)
        return record

    @staticmethod
    def reconcile_wagers(
        previous: tuple[WagerSnapshot, ...],
        current: tuple[WagerSnapshot, ...],
    ) -> tuple[WagerChange, ...]:

        previous_by_id = {
            wager.wager_id: wager
            for wager in previous
        }

        current_by_id = {
            wager.wager_id: wager
            for wager in current
        }

        changes = []

        # Removed or modified wagers
        for wager_id, before in previous_by_id.items():
            after = current_by_id.get(wager_id)

            if after is None:
                change_type = WagerChangeType.REMOVE

            elif before == after:
                continue

            elif before.value != after.value:
                change_type = WagerChangeType.ADJUST

            else:
                change_type = WagerChangeType.STATUS

            changes.append(
                WagerChange(
                    wager_id=wager_id,
                    player_id=before.player_id,
                    change_type=change_type,
                    before=before,
                    after=after,
                )
            )

        # Newly placed wagers
        for wager_id, after in current_by_id.items():
            if wager_id in previous_by_id:
                continue

            changes.append(
                WagerChange(
                    wager_id=wager_id,
                    player_id=after.player_id,
                    change_type=WagerChangeType.PLACE,
                    before=None,
                    after=after,
                )
            )

        return tuple(changes)

 
    @property
    def is_closed(self) -> bool:
        return self._closing_players is not None


    @property
    def closing_players(self) -> tuple[PlayerSnapshot, ...] | None:
        return self._closing_players


    @property
    def closing_wagers(self) -> tuple[WagerSnapshot, ...] | None:
        return self._closing_wagers


    def close(self, game: Game) -> None:
        if not self._opening_captured:
            raise RuntimeError(
                "Cannot close a session without an opening snapshot."
            )

        if self.is_closed:
            raise RuntimeError("Session is already closed.")

        self._closing_players = self.snapshot_players(game)
        self._closing_wagers = self.snapshot_wagers(game)
   

