from dataclasses import dataclass
from enum import Enum, auto
from engine import PlayerEquity, WagerType, Resolution

class WagerChangeType(Enum):
    PLACE = auto()
    REMOVE = auto()
    ADJUST = auto()
    STATUS = auto()

@dataclass(frozen=True)
class WagerSnapshot:
    wager_id: int
    player_id: int
    wager_type: WagerType
    value: int
    target: int | tuple[int, int] | None
    
    is_working: bool
    is_buy: bool
    collected_vig: int

    contract_min: int | None
    contract_max: int | None

    parent_wager_id: int | None


@dataclass(frozen=True)
class WagerChange:
    wager_id: int
    player_id: int
    change_type: WagerChangeType

    before: WagerSnapshot | None
    after: WagerSnapshot | None

    @property
    def value_change(self) -> int:
        return (
            (self.after.value if self.after else 0)
            - (self.before.value if self.before else 0)
        )

    @property
    def vig_change(self) -> int:
        return (
            (self.after.collected_vig if self.after else 0)
            - (self.before.collected_vig if self.before else 0)
        )


@dataclass(frozen=True)
class PlayerSnapshot:
    player_id: int
    name: str
    position: int
    equity: PlayerEquity


@dataclass(frozen=True)
class WagerOutcome:
    wager_id: int
    resolution: Resolution
    profit: int
    player_id: int
    move_to: int | None


@dataclass(frozen=True)
class RollRecord:
    roll_number: int

    # Dice and point information
    dice: tuple[int, int]
    point_before: int | None
    point_after: int | None

    # Shooter information
    shooter_id: int | None
    shooter_roll_count: int
    seven_out: bool

    # Player financial snapshots
    players_before: tuple[PlayerSnapshot, ...]
    players_after: tuple[PlayerSnapshot, ...]

    # Wager state snapshots
    wagers_before: tuple[WagerSnapshot, ...]
    wagers_after: tuple[WagerSnapshot, ...]
    wager_changes_before: tuple[WagerChange, ...]

    # Wager resolutions
    wager_outcomes: tuple[WagerOutcome, ...]



@dataclass(frozen=True)
class SessionFinancialSummary:
    player_id: int
    player_name: str

    roll_count: int

    opening_bankroll: int
    closing_bankroll: int

    opening_equity: int
    closing_equity: int
    net_equity_change: int

    closing_liquid_equity: int
    closing_reserved_equity: int
    outstanding_wager_value: int

    maximum_drawdown: int
    maximum_drawdown_pct: float

    wins: int
    losses: int
    pushes: int

    winning_profit: int
    lost_stakes: int
    net_resolution_result: int



