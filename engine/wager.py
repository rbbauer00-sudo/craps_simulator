from __future__ import annotations
from collections.abc import Callable
from typing import TYPE_CHECKING
from dataclasses import dataclass, field
from .exceptions import GameRuleViolation
from . import wager_rules as rules
from .enums import VigSetting, WagerType

if TYPE_CHECKING:
    from .player import Player
    from .dice import RollResult
    from .enums import WagerType, Resolution
    from .game import Game


type PlacementRule = Callable[
    [Wager], None,
]

type ResolutionRule = Callable[
    [Wager, RollResult],
    Resolution,
]

type PayoutRule = Callable[
    [Wager], int,
]

type PersistenceRule = Callable[
    [Wager], bool,
]

type ContractRule = Callable[
    [Wager], None,
]


@dataclass(frozen=True)
class WagerResult:
    wager: Wager
    resolution: Resolution
    profit: int = 0
    move_to: int | None = None


@dataclass(frozen=True)
class WagerDefinition:
    wager_type: WagerType
    name: str
    placement_rule: PlacementRule
    resolution_rule: ResolutionRule
    payout_rule: PayoutRule
    contract_rule: ContractRule = rules.no_contract
    can_turn_off: bool = False
    remove_after_win: bool = False


@dataclass(eq=False)
class Wager:
    definition: WagerDefinition
    player: Player
    game: Game
    value: int
    collected_vig: int = 0
    target: int | RollResult | None = None
    contract_min: int | None = None
    contract_max: int | None = None
    parent_wager: Wager | None = None
    _is_working: bool = True
    _is_buy: bool = False
    targets_hit: set[int] = field(default_factory=set)
    _id: int | None = field(default=None, init=False)

    @property
    def id(self) -> int:
        return self._id

    @property
    def is_working(self) -> bool:
        return self._is_working

    @is_working.setter
    def is_working(self, value: bool) -> None:
  
        if type(value) is not bool:
            raise TypeError(
                "Wager.is_working requires a bool; "
                f"received {type(value).__name__}: {value!r}."
            )
        
        allowed = self.definition.can_turn_off
        
        if not value and not self.definition.can_turn_off:
            raise GameRuleViolation(
                f"{self.definition.name} bets cannot be turned off."
            )
        
        self._is_working = value


    @property
    def is_buy(self) -> bool:
        """
        Returns the buy status of a wager.
        Intended only for place bets, other bet types return False.
        VigSetting.AUTOBUY will override manual placement if wager
        value is above auto_buy_level, as this is always advantageous 
        to the player. 
        """

        return (
            self._is_buy or (
                self.definition.wager_type is WagerType.PLACE_BET
                and self.target in (4,10)
                and self.value >= self.game.settings.auto_buy_level
                and self.game.settings.buy_vig_setting is(
                    VigSetting.AUTO_BUY
                )
            )
        )

    @is_buy.setter
    def is_buy(self, value: bool) -> None:
        """
        Intended only for place bets.
        Raises error if attempt to set any other bet type to True.
        """

        if type(value) is not bool:
            raise TypeError(
                "Wager.is_buy requires a bool; "
                f"received {type(value).__name__}: {value!r}."
            )

        if (
            self.definition.wager_type is not WagerType.PLACE_BET
            and value
        ):
            raise ValueError(
                "Buy status can only be enabled for "
                "PLACE_BET wagers; received "
                f"{self.definition.wager_type.name}."
            )

        self._is_buy = value

        
