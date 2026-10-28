from dataclasses import dataclass

from engine import WagerType


@dataclass
class WorkingPreferences:
    place_on_comeout: bool = False
    hardway_on_comeout: bool = True

    def default_status(
        self,
        wager_type: WagerType,
        point: int | None,
    ) -> bool | None:

        if wager_type is WagerType.PLACE_BET:
            return (
                self.place_on_comeout
                if point is None
                else True
            )

        if wager_type is WagerType.HARDWAY:
            return (
                self.hardway_on_comeout
                if point is None
                else True
            )

        # No automatic working-status management
        # for other wager types.
        return None