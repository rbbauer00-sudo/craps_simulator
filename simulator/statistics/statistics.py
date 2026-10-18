from collections import Counter
from dataclasses import dataclass
from engine import GameRollResult




class Statistics:
    def __init__(self):
        self.roll_count = 0
        self.roll_frequencies = Counter()
        self.seven_outs = 0
        self.points_made = 0

    def record_roll(self, result: GameRollResult) -> None:
        self.roll_count += 1
        self.roll_frequencies[result.roll.total] += 1

        if result.seven_out:
            self.seven_outs += 1

        if (
            result.point_before is not None
            and result.roll.total == result.point_before
        ):
            self.points_made += 1