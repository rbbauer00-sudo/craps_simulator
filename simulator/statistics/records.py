from dataclasses import dataclass
from engine import PlayerEquity, WagerType, Game, Resolution
from statistics import W


@dataclass(frozen=True)
class PlayerSnapshot:
    player_id: int
    name: str
    position: int
    equity: PlayerEquity


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

    # Wager resolutions
    wager_outcomes: tuple[WagerOutcome, ...]