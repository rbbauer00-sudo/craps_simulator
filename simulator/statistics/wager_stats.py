
from collections import Counter
from collections.abc import Sequence

from engine import WagerType, Resolution

from .records import RollRecord, WagerSnapshot


class WagerStatistics:

    def __init__(
        self,
        rolls: Sequence[RollRecord],
        player_id: int | None = None,
        wager_type: WagerType | None = None,
    ) -> None:

        self._rolls = tuple(rolls)
        self.player_id = player_id
        self.wager_type = wager_type

        self._events = []

        for record in self._rolls:
            before_by_id = {
                wager.wager_id: wager
                for wager in record.wagers_before
            }

            for outcome in record.wager_outcomes:
                wager = before_by_id[outcome.wager_id]

                if (
                    self.player_id is not None
                    and wager.player_id != self.player_id
                ):
                    continue

                if (
                    self.wager_type is not None
                    and wager.wager_type is not self.wager_type
                ):
                    continue

                self._events.append((outcome, wager))

    @property
    def resolution_counts(self) -> Counter[Resolution]:
        return Counter(
            outcome.resolution
            for outcome, _ in self._events
        )

    @property
    def wins(self) -> int:
        return self.resolution_counts[Resolution.WIN]

    @property
    def losses(self) -> int:
        return self.resolution_counts[Resolution.LOSE]

    @property
    def pushes(self) -> int:
        return self.resolution_counts[Resolution.PUSH]

    @property
    def moves(self) -> int:
        return self.resolution_counts[Resolution.MOVE]

    @property
    def win_rate(self) -> float:
        resolved = self.wins + self.losses
        return self.wins / resolved if resolved else 0.0

    @property
    def winning_profit(self) -> int:
        return sum(
            outcome.profit
            for outcome, _ in self._events
            if outcome.resolution is Resolution.WIN
        )

    @property
    def lost_stakes(self) -> int:
        return sum(
            wager.value
            for outcome, wager in self._events
            if outcome.resolution is Resolution.LOSE
        )

    @property
    def net_resolution_result(self) -> int:
        return self.winning_profit - self.lost_stakes

    @property
    def outcomes_by_type(self) -> dict[WagerType, Counter]:
        result = {}

        for outcome, wager in self._events:
            if wager.wager_type not in result:
                result[wager.wager_type] = Counter()

            result[wager.wager_type][outcome.resolution] += 1

        return result

    @property
    def resolved_wager_amount(self) -> int:
        return sum(
            wager.value
            for outcome, wager in self._events
            if outcome.resolution in (
                Resolution.WIN,
                Resolution.LOSE,
            )
        )

    @property
    def roll_exposure(self) -> int:
        return sum(
            wager.value
            for outcome, wager in self._events
            if wager.is_working
        )

    @property
    def net_return_on_resolved_amount(self) -> float:
        amount = self.resolved_wager_amount

        return (
            self.net_resolution_result / amount
            if amount else 0.0
        )