
from collections.abc import Sequence

from .records import RollRecord, PlayerSnapshot


class PlayerStatistics:

    def __init__(
        self,
        rolls: Sequence[RollRecord],
        player_id: int,
        opening_snapshot: PlayerSnapshot | None = None,
        closing_snapshot: PlayerSnapshot | None = None,
    ) -> None:
        self._rolls = tuple(rolls)
        self.player_id = player_id
        self._opening_snapshot = opening_snapshot
        self._closing_snapshot = closing_snapshot

        self._before = []
        self._after = []

        for record in self._rolls:
            before = self._find_player(
                record.players_before
            )
            after = self._find_player(
                record.players_after
            )

            if before is not None and after is not None:
                self._before.append(before.equity)
                self._after.append(after.equity)


    def _find_player(
        self,
        snapshots: tuple[PlayerSnapshot, ...],
    ) -> PlayerSnapshot | None:
        return next(
            (
                snapshot
                for snapshot in snapshots
                if snapshot.player_id == self.player_id
            ),
            None,
        )


    @property
    def roll_count(self) -> int:
        return len(self._after)


    @property
    def starting_equity(self) -> int:
        if self._opening_snapshot is not None:
            return self._opening_snapshot.equity.total_equity

        return (
            self._before[0].total_equity
            if self._before else 0
        )

    @property
    def ending_equity(self) -> int:
        if self._closing_snapshot is not None:
            return self._closing_snapshot.equity.total_equity

        if self._after:
            return self._after[-1].total_equity

        if self._opening_snapshot is not None:
            return self._opening_snapshot.equity.total_equity

        return 0


    @property
    def equity_curve(self) -> tuple[int, ...]:
        if (
            self._opening_snapshot is None
            and not self._before
            and self._closing_snapshot is None
        ):
            return ()

        curve = (
            self.starting_equity,
            *self.equity_history,
        )

        if (
            self._closing_snapshot is not None
            and curve[-1] != self.ending_equity
        ):
            curve += (self.ending_equity,)

        return curve


    @property
    def net_profit(self) -> int:
        return self.ending_equity - self.starting_equity
    
    @property
    def equity_history(self) -> tuple[int, ...]:
        return tuple(
            equity.total_equity
            for equity in self._after
        )

    @property
    def bankroll_history(self) -> tuple[int, ...]:
        return tuple(
            equity.bankroll
            for equity in self._after
        )

    @property
    def liquid_equity_history(self) -> tuple[int, ...]:
        return tuple(
            equity.liquid_equity
            for equity in self._after
        )

    @property
    def peak_equity(self) -> int:
        return max(self.equity_curve, default=0)

    @property
    def maximum_drawdown(self) -> int:
        peak = None
        largest_drawdown = 0

        for equity in self.equity_curve:
            peak = (
                equity if peak is None
                else max(peak, equity)
            )
            largest_drawdown = max(
                largest_drawdown,
                peak - equity,
            )

        return largest_drawdown

    @property
    def maximum_drawdown_pct(self) -> float:
        peak = None
        largest_pct = 0.0

        for equity in self.equity_curve:
            peak = (
                equity if peak is None
                else max(peak, equity)
            )

            if peak > 0:
                largest_pct = max(
                    largest_pct,
                    (peak - equity) / peak,
                )

        return largest_pct


    @property
    def closing_bankroll(self) -> int:
        if self._closing_snapshot is not None:
            return self._closing_snapshot.equity.bankroll

        if self._after:
            return self._after[-1].bankroll

        if self._opening_snapshot is not None:
            return self._opening_snapshot.equity.bankroll

        return 0


    @property
    def closing_liquid_equity(self) -> int:
        if self._closing_snapshot is not None:
            return self._closing_snapshot.equity.liquid_equity

        if self._after:
            return self._after[-1].liquid_equity

        if self._opening_snapshot is not None:
            return self._opening_snapshot.equity.liquid_equity

        return 0