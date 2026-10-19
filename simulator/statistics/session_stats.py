
from collections.abc import Sequence
from functools import cached_property

from engine import WagerType

from .records import RollRecord, PlayerSnapshot, WagerSnapshot, SessionFinancialSummary
from .dice_stats import DiceStatistics
from .shooter_stats import ShooterStatistics
from .player_stats import PlayerStatistics
from .wager_stats import WagerStatistics


class SessionStatistics:

    def __init__(
        self,
        rolls: Sequence[RollRecord],
        opening_players: Sequence[PlayerSnapshot] = (),
        closing_players: Sequence[PlayerSnapshot] = (),
        closing_wagers: Sequence[WagerSnapshot] = (),
    ) -> None:
        self._rolls = tuple(rolls)
        self._opening_players = tuple(opening_players)
        self._closing_players = tuple(closing_players)
        self._closing_wagers = tuple(closing_wagers)

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
            p.player_id
            for p in (
                *self._opening_players,
                *self._closing_players,
            )
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
            p.player_id: p
            for p in self._opening_players
        }

        closing_by_id = {
            p.player_id: p
            for p in self._closing_players
        }

        return {
            player_id: PlayerStatistics(
                self._rolls,
                player_id,
                opening_snapshot=opening_by_id.get(player_id),
                closing_snapshot=closing_by_id.get(player_id),
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

    
    def financial_summary(
        self,
        player_id: int,
    ) -> SessionFinancialSummary:
        opening = next(
            (
                p for p in self._opening_players
                if p.player_id == player_id
            ),
            None,
        )

        closing = next(
            (
                p for p in self._closing_players
                if p.player_id == player_id
            ),
            None,
        )

        if opening is None or closing is None:
            raise ValueError(
                "A financial summary requires opening and "
                "closing snapshots for the player."
            )

        player_stats = self.player(player_id)
        wager_stats = self.wager_stats(player_id=player_id)

        outstanding = sum(
            wager.value
            for wager in self._closing_wagers
            if wager.player_id == player_id
        )

        return SessionFinancialSummary(
            player_id=player_id,
            player_name=closing.name,
            roll_count=player_stats.roll_count,

            opening_bankroll=opening.equity.bankroll,
            closing_bankroll=closing.equity.bankroll,

            opening_equity=opening.equity.total_equity,
            closing_equity=closing.equity.total_equity,
            net_equity_change=(
                closing.equity.total_equity
                - opening.equity.total_equity
            ),

            closing_liquid_equity=(
                closing.equity.liquid_equity
            ),
            closing_reserved_equity=(
                closing.equity.reserved_equity
            ),
            outstanding_wager_value=outstanding,

            maximum_drawdown=player_stats.maximum_drawdown,
            maximum_drawdown_pct=(
                player_stats.maximum_drawdown_pct
            ),

            wins=wager_stats.wins,
            losses=wager_stats.losses,
            pushes=wager_stats.pushes,

            winning_profit=wager_stats.winning_profit,
            lost_stakes=wager_stats.lost_stakes,
            net_resolution_result=(
                wager_stats.net_resolution_result
            ),
        )

