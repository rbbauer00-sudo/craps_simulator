
from collections import Counter
from collections.abc import Sequence
from statistics import mean

from .records import RollRecord


class ShooterStatistics:

    def __init__(self, rolls: Sequence[RollRecord]):
        self._rolls = tuple(rolls)

    @property
    def total_rolls(self) -> int:
        return len(self._rolls)

    @property
    def completed_hands(self) -> int:
        return sum(
            record.seven_out
            for record in self._rolls
        )

    @property
    def seven_outs(self) -> int:
        return self.completed_hands

    @property
    def hand_lengths(self) -> tuple[int, ...]:
        return tuple(
            record.shooter_roll_count
            for record in self._rolls
            if record.seven_out
        )

    @property
    def average_hand_length(self) -> float:
        return (
            mean(self.hand_lengths)
            if self.hand_lengths
            else 0.0
        )

    @property
    def longest_hand(self) -> int:
        return max(self.hand_lengths, default=0)

    @property
    def shortest_hand(self) -> int:
        return min(self.hand_lengths, default=0)

    @property
    def active_hand_length(self) -> int:
        if not self._rolls:
            return 0

        last = self._rolls[-1]

        return (
            0
            if last.seven_out
            else last.shooter_roll_count
        )

    @property
    def points_established(self) -> int:
        return sum(
            record.point_before is None
            and record.point_after is not None
            for record in self._rolls
        )

    @property
    def points_made(self) -> int:
        return sum(
            record.point_before is not None
            and sum(record.dice) == record.point_before
            for record in self._rolls
        )

    @property
    def point_make_rate(self) -> float:
        return (
            self.points_made / self.points_established
            if self.points_established
            else 0.0
        )

    @property
    def rolls_by_shooter(self) -> Counter[int]:
        return Counter(
            record.shooter_id
            for record in self._rolls
            if record.shooter_id is not None
        )

    @property
    def hands_by_shooter(self) -> Counter[int]:
        return Counter(
            record.shooter_id
            for record in self._rolls
            if record.seven_out
            and record.shooter_id is not None
        )

    @property
    def points_made_by_shooter(self) -> Counter[int]:
        return Counter(
            record.shooter_id
            for record in self._rolls
            if record.shooter_id is not None
            and record.point_before is not None
            and sum(record.dice) == record.point_before
        )

