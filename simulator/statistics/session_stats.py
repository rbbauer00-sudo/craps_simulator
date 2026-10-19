
from collections.abc import Sequence
from functools import cached_property

from engine import WagerType

from .records import RollRecord, PlayerSnapshot
from .dice_stats import DiceStatistics
from .shooter_stats import ShooterStatistics
from .player_stats import PlayerStatistics
from .wager_stats import WagerStatistics


class SessionStatistics:

    def __init__(
        self,
        rolls: Sequence[RollRecord],
        opening_players: Sequence[PlayerSnapshot] = (),
    ) -> None:
        # Freeze the session input.
        self._rolls = tuple(rolls)
        self._opening_players = tuple(opening_players)

    @property
    def roll_count(self) -> int:
        return len(self._rolls)

    @property
    def rolls(self) -> tuple[RollRecord, ...]:
        return self._rolls

    @cached_property
    def dice(self) -> DiceStatistics:
        return DiceStatistics(self._rolls)

    @cached_property
    def shooters(self) -> ShooterStatistics:
        return ShooterStatistics(self._rolls)

    @cached_property
    def wagers(self) -> WagerStatistics:
        return WagerStatistics(self._rolls)

    @cached_property
    def player_ids(self) -> tuple[int, ...]:
        ids = {
            player.player_id
            for player in self._opening_players
        }

        for record in self._rolls:
            for snapshot in (
                *record.players_before,
                *record.players_after,
            ):
                ids.add(snapshot.player_id)

        return tuple(sorted(ids))

    @cached_property
    def players(self) -> dict[int, PlayerStatistics]:
        opening_by_id = {
            snapshot.player_id: snapshot
            for snapshot in self._opening_players
        }

        return {
            player_id: PlayerStatistics(
                self._rolls,
                player_id,
                opening_snapshot=opening_by_id.get(player_id),
            )
            for player_id in self.player_ids
        }

    def player(
        self,
        player_id: int,
    ) -> PlayerStatistics:
        return self.players[player_id]

    def wager_stats(
        self,
        player_id: int | None = None,
        wager_type: WagerType | None = None,
    ) -> WagerStatistics:
        if player_id is None and wager_type is None:
            return self.wagers

        return WagerStatistics(
            self._rolls,
            player_id=player_id,
            wager_type=wager_type,
        )
