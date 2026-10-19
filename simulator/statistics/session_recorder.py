from dataclasses import dataclass
from engine import Game, GameRollResult
from .records import (
    PlayerSnapshot,
    WagerSnapshot,
    RollRecord,
)


class SessionRecorder:
    def __init__(self):
        self._rolls: list[RollRecord] = []

    @property
    def rolls(self) -> tuple[RollRecord, ...]:
        return tuple(self._rolls)

    @property
    def roll_count(self) -> int:
        return len(self._rolls)

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
    ) -> RollRecord:

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
            wager_results=result.wager_results,
        )

        self._rolls.append(record)
        return record

    def clear(self) -> None:
        self._rolls.clear()