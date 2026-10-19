from collections import Counter
from collections.abc import Sequence

from .records import RollRecord



class DiceStatistics:
    EXPECTED_COMBINATIONS = {
        2: 1, 3: 2, 4: 3, 5: 4, 6: 5,
        7: 6,
        8: 5, 9: 4, 10: 3, 11: 2, 12: 1,
    }

    def __init__(self, rolls: Sequence[RollRecord]):
        self._rolls = rolls

    @property
    def total_rolls(self) -> int:
        return len(self._rolls)

    @property
    def total_frequencies(self) -> Counter[int]:
        return Counter(
            sum(record.dice)
            for record in self._rolls
        )

    @property
    def combination_frequencies(
        self,
    ) -> Counter[tuple[int, int]]:
        return Counter(
            tuple(sorted(record.dice))
            for record in self._rolls
        )

    @property
    def seven_count(self) -> int:
        return self.total_frequencies[7]

    @property
    def hardway_count(self) -> int:
        return sum(
            1
            for record in self._rolls
            if record.dice[0] == record.dice[1]
            and sum(record.dice) in (4, 6, 8, 10)
        )

    def expected_count(self, total: int) -> float:
        if total not in self.EXPECTED_COMBINATIONS:
            raise ValueError(f"Invalid dice total: {total}")

        return (
            self.total_rolls
            * self.EXPECTED_COMBINATIONS[total]
            / 36
        )