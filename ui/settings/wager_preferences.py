from dataclasses import dataclass, field

from engine import WagerType


AUTO_TAKE_DOWN_ELIGIBLE = frozenset({
    WagerType.FIELD,
    WagerType.HOP,
    WagerType.HARDWAY,
    WagerType.ANY_SEVEN,
    WagerType.ANY_CRAPS,
    WagerType.YO_LEVEN,
    WagerType.ACE_DEUCE,
    WagerType.DEUCE,
    WagerType.MIDNIGHT,
})


@dataclass
class WagerPreferences:
    take_down_on_win: dict[WagerType, bool] = field(
        default_factory=dict
    )

    def should_take_down(self, wager) -> bool:
        wager_type = wager.definition.wager_type

        return (
            wager_type in AUTO_TAKE_DOWN_ELIGIBLE
            and self.take_down_on_win.get(
                wager_type,
                False,
            )
        )