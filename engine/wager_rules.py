from __future__ import annotations
from collections.abc import Callable, Collection
from typing import TYPE_CHECKING
from .enums import Resolution, WagerType, VigSetting
from .exceptions import GameRuleViolation, EngineStateError
from .dice import RollResult
from . import constants as const

if TYPE_CHECKING:
    from .wager import Wager
    from .game import Game

type ResolutionRule = Callable[
    [Wager, RollResult],
    Resolution,
]



#====================================================
# PLACEMENT RULES -> None #Raises error if violated.
#====================================================

def require_point_on(
    wager: Wager,
) -> None:
   
    if wager.game.point is None:
        raise GameRuleViolation(
            f"{wager.definition.name} can only be "
            "placed when the point is ON."
        )


def require_point_off(
    wager: Wager,
) -> None:

    if wager.game.point is not None:
        raise GameRuleViolation(
            f"{wager.definition.name} can only be "
                "placed when the point is OFF."
            )


def require_target_is_none(
    wager: Wager,    
):
    if wager.target is not None:
        raise ValueError(
            f"Unexpected wager target for "
            f"{wager.definition.wager_type.name}: "
            f"{wager.target}.  "
            "Expected wager target: None."
        )


def require_target_in_set(
    wager: Wager,
    target_set: Collection[int | tuple[int, int]],
) -> None:

    if wager.target not in target_set:

        raise ValueError(
            f"Unexpected wager target for "
            f"{wager.definition.wager_type.name}: "
            f"{wager.target}.  "
            "Expected wager targets: "
            f"{target_set}."
        )


def validate_no_duplicates(
    wager: Wager,
) -> None:

    for existing in wager.game.wagers:
        if (
            existing.player is wager.player
            and existing.target == wager.target
            and existing.definition.wager_type
                is wager.definition.wager_type
        ):
            description = wager.definition.name

            if wager.target is not None:
                description += f" on {wager.target}"

            raise GameRuleViolation(
                f"You already have a {description} wager."
            )


def require_no_existing_child(
    wager: Wager,
) -> None:

    parent = wager.parent_wager

    if parent is None:
        raise ValueError(
            f"{wager.definition.wager_type.name} "
            "requires a parent_wager reference."
        )

    if wager.game.get_child_wager(parent) is not None:
        raise GameRuleViolation(
            "This wager already has an odds bet. "
            "Adjust or remove the existing odds first."
        )


def validate_prop_placement(
    wager: Wager,
) -> None:

    validate_no_duplicates(wager)
    require_target_is_none(wager)


def validate_hardway_placement(
    wager: Wager,
) -> None:

    validate_no_duplicates(wager)
    require_target_in_set(
        wager,
        target_set={4, 6, 8, 10},
    )


def validate_hop_placement(
    wager: Wager,
) -> None:

    target = wager.target

    if (
        not isinstance(target, tuple)
        or len(target) != 2
        or not all(
            type(die) is int and 1 <= die <= 6
            for die in target
        )
    ):
        raise ValueError(
            f"Invalid Hop target {target!r}; "
            "expected a tuple of two dice values (1-6)."
        )

    wager.target = tuple(sorted(target))

    require_target_in_set(
        wager,
        target_set=const.HOP_TARGETS,
    )

    validate_no_duplicates(wager)


def validate_pass_line_placement(
    wager: Wager,
) -> None:

    validate_no_duplicates(wager)

    require_target_is_none(wager)

    if (
        wager.game.point is not None
        and not wager.game.settings.allow_put_bets
    ):
        raise GameRuleViolation(
            "Pass Line bets cannot be placed after "
            "the point is established at this table."
        )

    
def validate_come_placement(
    wager: Wager,
) -> None:

    validate_no_duplicates(wager)
    require_point_on(wager)

    if wager.target is not None:
        if not wager.game.settings.allow_put_bets:
            raise GameRuleViolation(
                "Put Come bets are not allowed "
                "at this table."
            )

        require_target_in_set(
            wager,
            target_set=const.BOX_NUMS,
        )

        if wager.target == wager.game.point:
            raise GameRuleViolation(
                "Put Come bet cannot be placed on the "
                f"current point of {wager.game.point}."
            )


def validate_dont_pass_placement(
    wager: Wager,
) -> None:

    validate_no_duplicates(wager)
    require_point_off(wager)
    require_target_is_none(wager)

    
def validate_dont_come_placement(
    wager: Wager,
) -> None:

    validate_no_duplicates(wager)
    require_point_on(wager)
    require_target_is_none(wager)


def validate_line_odds_placement(
    wager: Wager,
) -> None:
    
    parent = wager.parent_wager

    # 1. Validate parent reference
    if parent is None:
        raise ValueError(
            "LINE_ODDS requires a parent_wager; "
            "received None."
        )

    # 2. Validate parent type
    parent_type = parent.definition.wager_type

    if parent_type not in {
        WagerType.PASS_LINE,
        WagerType.COME,
    }:
        raise ValueError(
            "LINE_ODDS requires a PASS_LINE or COME "
            f"parent; received {parent_type.name}."
        )

    # 3. Validate parent ownership
    if parent.player is not wager.player:
        raise ValueError(
            "LINE_ODDS parent and child wagers "
            "belong to different players."
        )

    # 4. Validate active parent
    if parent.game is not wager.game:
        raise ValueError(
            "Odds parent belongs to a different Game instance."
        )

    if parent not in wager.game.wagers:
        raise GameRuleViolation(
            "You must have an active Pass Line or "
            "Come bet before adding odds."
        )

    # 5. Check existing odds
    require_no_existing_child(wager)

    # 6. Determine odds target
    odds_target = (
        parent.target
        if parent_type is WagerType.COME
        else wager.game.point
    )

    if odds_target is None:
        raise GameRuleViolation(
            "Odds cannot be added until the "
            "parent wager has an established point."
        )

    # 7. Validate derived target
    if odds_target not in const.BOX_NUMS:
        raise EngineStateError(
            f"LINE_ODDS derived invalid target "
            f"{odds_target!r} from "
            f"{parent_type.name} parent."
        )

    # 8. Assign target and check duplicates
    wager.target = odds_target

    validate_no_duplicates(wager)


def validate_lay_odds_placement(
    wager: Wager,
) -> None:

    
    parent = wager.parent_wager

    if parent is None:
        raise ValueError(
            "LAY_ODDS requires a parent_wager; "
            "received None."
        )

    parent_type = parent.definition.wager_type

    if parent_type not in {
        WagerType.DONT_PASS,
        WagerType.DONT_COME,
    }:
        raise ValueError(
            "LAY_ODDS requires a DONT_PASS or "
            f"DONT_COME parent; received {parent_type.name}."
        )

    if parent.player is not wager.player:
        raise ValueError(
            "LAY_ODDS parent and child wagers "
            "belong to different players."
        )

    if parent.game is not wager.game:
        raise ValueError(
            "Odds parent belongs to a different Game instance."
        )

    if parent not in wager.game.wagers:
        raise GameRuleViolation(
            "You must have an active Don't Pass "
            "or Don't Come bet before adding odds."
        )

    require_no_existing_child(wager)

    odds_target = (
        parent.target
        if parent_type is WagerType.DONT_COME
        else wager.game.point
    )

    if odds_target is None:
        raise GameRuleViolation(
            "Odds cannot be added until the "
            "parent wager has an established point."
        )

    if odds_target not in const.BOX_NUMS:
        raise EngineStateError(
            f"LAY_ODDS derived invalid target "
            f"{odds_target!r} from "
            f"{parent_type.name} parent."
        )

    wager.target = odds_target

    validate_no_duplicates(wager)


def validate_place_lay_bet_placement(
    wager: Wager,
) -> None:

    validate_no_duplicates(wager)
    require_target_in_set(
        wager,
        target_set=const.BOX_NUMS
    )


def validate_ats_placement(
        wager: Wager,
) -> None:
    
    last_roll = wager.game.get_last_roll()

    if not (
        wager.game.shooter_roll_count == 0
        or (
            last_roll is not None
            and last_roll.total == 7
        )
    ):
        raise GameRuleViolation(
            "ATS wagers can only be placed before "
            "a new shooter's first roll or immediately "
            "after a seven."
        ) 

    targets = {
        WagerType.ATS_SMALL: const.ATS_SMALL_NUMS,
        WagerType.ATS_TALL: const.ATS_TALL_NUMS,
        WagerType.ATS_ALL: const.ATS_ALL_NUMS,
    }

    wager_type = wager.definition.wager_type

    if wager_type not in targets:
        raise ValueError(
            "validate_ats_placement received unsupported "
            f"wager type {wager_type!r}."
    )

    wager.target = targets[wager_type]

    validate_no_duplicates(
        wager
    )


def validate_fire_bet_placement(
        wager: Wager,
) -> None:

    if not (
            wager.game.shooter_roll_count == 0
        ):
            raise GameRuleViolation(
                "Fire Bets can only be placed before "
                "a new shooter's first roll."
            ) 
    
    wager.target = const.BOX_NUMS
    wager.targets_hit = set()

    validate_no_duplicates(
        wager
    )


#=================================================
# RESOLUTION RULES -> Resoution
#=================================================

def simple_resolution(
    winning_totals: set[int],
    losing_totals: set[int] = const.ALL_NUMS
) -> ResolutionRule:

    def resolution_rule(
        wager: Wager, 
        roll: RollResult,
    ) -> Resolution:
        
        roll_total = roll.total
        
        if roll_total in winning_totals:
            return Resolution.WIN

        elif roll_total in losing_totals:
            return Resolution.LOSE

        return Resolution.NONE

    return resolution_rule


def pass_line_resolution(
    wager: Wager,
    roll: RollResult,
) -> Resolution:
    
    roll_total = roll.total

    if wager.game.point is not None:
        if roll_total == wager.game.point:
            return Resolution.WIN

        elif roll_total == 7:
            return Resolution.LOSE

    else: 
        if roll_total in {7, 11}:
            return Resolution.WIN
        
        elif roll_total in {2, 3, 12}:
            return Resolution.LOSE
    
    return Resolution.NONE


def dont_pass_resolution(
    wager: Wager,
    roll: RollResult,
) -> Resolution:

    roll_total = roll.total

    if wager.game.point is not None:
        if roll_total == wager.game.point:
            return Resolution.LOSE

        elif roll_total == 7:
            return Resolution.WIN

    else:
        if roll_total in {7, 11}:
            return Resolution.LOSE

        elif roll_total in {2, 3}:
           return Resolution.WIN
        
        elif roll_total == 12:
           return Resolution.PUSH
            
    return Resolution.NONE


def come_bet_resolution(
    wager: Wager,
    roll: RollResult,
) -> Resolution:

    roll_total = roll.total

    # Still sitting in the Come Box
    if wager.target is None:

        if roll_total in {7, 11}:
            return Resolution.WIN

        elif roll_total in {2, 3, 12}:
           return Resolution.LOSE

        elif roll_total in {4, 5, 6, 8, 9, 10}:
            return Resolution.MOVE
            
    # Travelled Come bet
    else:
        if roll_total == wager.target:
            return Resolution.WIN

        elif roll_total == 7:
            return Resolution.LOSE

    return Resolution.NONE


def dont_come_resolution(
    wager: Wager,
    roll: RollResult,
) -> Resolution:

    roll_total = roll.total

    # Still sitting in the DC Box
    if wager.target is None:

        if roll_total in {7, 11}:
            return Resolution.LOSE

        elif roll_total in {2, 3}:
           return Resolution.WIN
        
        elif roll_total == 12:
           return Resolution.PUSH

        elif roll_total in {4, 5, 6, 8, 9, 10}:
            return Resolution.MOVE
            
    # Travelled DC bet
    else:
        if roll_total == wager.target:
            return Resolution.LOSE

        elif roll_total == 7:
            return Resolution.WIN

    return Resolution.NONE


def line_odds_resolution(
    wager: Wager,
    roll: RollResult,
) -> Resolution:

    if not wager.is_working:
        parent_result = (
            wager.game._get_single_wager_result(
                wager.parent_wager,
                roll
            )
        )

        if parent_result.resolution in (
            Resolution.WIN,
            Resolution.LOSE,
        ):
            return Resolution.REMOVE

    else:    
        if roll.total == wager.target:
            return Resolution.WIN

        if roll.total == 7:
            return Resolution.LOSE

    return Resolution.NONE


def lay_odds_resolution(
    wager: Wager,
    roll: RollResult,
) -> Resolution:

    if not wager.is_working:
        parent_result = (
            wager.game._get_single_wager_result(
                wager.parent_wager,
                roll
            )
        )

        if parent_result.resolution in (
            Resolution.WIN,
            Resolution.LOSE,
        ):
            return Resolution.REMOVE

    else:    
        if roll.total == 7:
            return Resolution.WIN

        if roll.total == wager.target:
            return Resolution.LOSE

    return Resolution.NONE


def hardway_resolution(
    wager: Wager,
    roll: RollResult,
) -> Resolution:

    if not wager.is_working:
        return Resolution.NONE

    if roll.total == 7:
        return Resolution.LOSE

    if roll.total != wager.target:
        return Resolution.NONE

    if roll.d1 == roll.d2:
        return Resolution.WIN

    return Resolution.LOSE


def hop_resolution(
    wager: Wager,
    roll: RollResult,
) -> Resolution:
    
    if roll.as_tuple == wager.target:
        return Resolution.WIN

    return Resolution.LOSE


def place_bet_resolution(
    wager: Wager,
    roll: RollResult,
) -> Resolution:

    if wager.is_working:

        if roll.total == wager.target:
            return Resolution.WIN

        if roll.total == 7:
            return Resolution.LOSE

    return Resolution.NONE


def lay_bet_resolution(
    wager: Wager,
    roll: RollResult,
) -> Resolution:
    
    if roll.total == 7:
        return Resolution.WIN

    if roll.total == wager.target:
        return Resolution.LOSE

    return Resolution.NONE


def ats_resolution(
    wager: Wager,
    roll: RollResult,
) -> Resolution:

    if roll.total == 7:
        return Resolution.LOSE
    
    if roll.total in (
        wager.target - wager.targets_hit
    ):
        wager.targets_hit.add(roll.total)

        if wager.targets_hit == wager.target:
            return Resolution.WIN

    return Resolution.NONE


def fire_bet_resolution(
    wager: Wager,
    roll: RollResult,
) -> Resolution:

    # Seven-out
    if (
        roll.total == 7
        and wager.game.point is not None
    ):
        if len(wager.targets_hit) >= 4:
            return Resolution.WIN 
        return Resolution.LOSE

    # Point made
    if (
        wager.game.point is not None
        and roll.total == wager.game.point
    ):
        wager.targets_hit.add(roll.total)

        if len(wager.targets_hit) >= 6:
            return Resolution.WIN

    return Resolution.NONE


#=================================================
# PAYOUT RULES -> int #profit
#=================================================

def fixed_multiple_payout(
        multiple: int, 
) -> Callable[[Wager], int]:
    
    func_name = f"pays_{multiple}_to_1"
    
    def payout_function(
        wager: Wager,
    ) -> int:
        return wager.value * multiple

    payout_function.__name__ = func_name

    return payout_function


def hardway_payout(
    wager: Wager,
) -> int:
    if wager.target in {4,10}:
        return wager.value * 7
    return wager.value * 9


def hop_payout(
    wager: Wager,
) -> int:

    d1, d2 = wager.target

    return(
        wager.value * 30
        if d1 == d2
        else wager.value * 15
    )


def field_payout(
    wager: Wager,
) -> int:
    roll = wager.game.get_last_roll().total

    if roll == 12 and wager.game.settings.field_3x_on_12:
        return wager.value * 3

    elif roll in (2, 12):
        return wager.value * 2

    return wager.value


def even_money_payout(
    wager: Wager,
) -> int:
    
    return wager.value


def line_odds_payout(
    wager: Wager,
) -> int:

    parent = wager.parent_wager
    parent_type = parent.definition.wager_type

    if parent_type not in (
        WagerType.PASS_LINE, 
        WagerType.COME,
    ):
        raise ValueError(
            "LINE_ODDS payout requires PASS_LINE "
            "or COME parent; received "
            f"{parent_type}."
        )

    match wager.target:
        case 4 | 10:
            n, d = (2, 1)

        case 5 | 9:
            n, d = (3, 2)

        case 6 | 8:
            n, d = (6, 5)

        case _:
            raise EngineStateError(
                "LINE_ODDS payout received invalid "
                f"target {wager.target}.  Expected "
                "targets: {4, 5, 6, 8, 9, 10}."
            )

    return wager.value * n // d


def lay_odds_payout(
    wager: Wager,
) -> int:

    parent = wager.parent_wager
    parent_type = parent.definition.wager_type

    if parent_type not in (
            WagerType.DONT_PASS, 
            WagerType.DONT_COME,
        ):
            raise ValueError(
                "LAY_ODDS payout requires DONT_PASS "
                "or DONT_COME parent; received "
                f"{parent_type}."
            )

    odds_target = (
        parent.target
        if parent_type is WagerType.DONT_COME
        else wager.game.point
    )
    
    match odds_target:
        case 4 | 10:
            n, d = (1, 2)

        case 5 | 9:
            n, d = (2, 3)

        case 6 | 8:
            n, d = (5, 6)

        case _:
            raise EngineStateError(
                "LAY_ODDS payout received invalid "
                f"target {odds_target}.  Expected "
                "targets: {4, 5, 6, 8, 9, 10}."
            )

    return wager.value * n // d


def place_bet_payout(
    wager: Wager,
) -> int:
    """
    If VigSetting is ON_WIN or AUTOBUY, vig is deducted 
    from wager payout to cover the current wager's vig.
    Since bets stay up by default,  the vig for the next
    wager must also be deducted from payout when 
    VigSetting.UP_FRONT to cover the replacent wager.
    Up front vig will be refunded if the new bet is taken 
    down by the player.  Wager.is_buy() returns false only 
    in the setting of a true regular place bet.  
    Game.calculate_vig() returns 0 when is_buy is false.
    """
    
    match wager.target:
        case 4 | 10:
            n, d = (
                 (2, 1) if wager.is_buy
                else (9, 5)
            )

        case 5 | 9:
            n,d  = (
                (3, 2) if wager.is_buy
                else (7, 5)
            )

        case 6 | 8:
            n,d  = (
                (6, 5) if wager.is_buy
                else (7, 6)
            )

        case _:
            raise EngineStateError(
                "PLACE_BET payout received invalid "
                f"target: {wager.target}. Expected "
                "targets: {4, 5, 6, 8, 9, 10}."
            )


    vig = wager.game.calculate_vig(wager)

    return max(0, wager.value * n // d - vig)


def lay_bet_payout(
    wager: Wager,
) -> int:
    match wager.target:
        case 4 | 10:
            n, d = (1, 2)

        case 5 | 9:
            n,d  = (2, 3)

        case 6 | 8:
            n,d  = (5, 6)

        case _:
            raise EngineStateError(
                "LAY_BET payout received invalid "
                f"target: {wager.target}. Expected "
                "targets: {4, 5, 6, 8, 9, 10}."
            )

    # Because lay bets stay up by default, the vig for the next
    # wager is deducted from winnings.  This value will be refunded
    # if the new wager is taken down by player.
    next_wager_vig = wager.game.calculate_vig(wager)
    return max(0, wager.value * n // d - next_wager_vig)


def fire_bet_payout(
    wager: Wager,
):
    points_hit = len(wager.targets_hit)

    match points_hit:

        case 6:
            return wager.value * 999
        
        case 5:
            return wager.value * 249
        
        case 4:
            return wager.value * 24
        
        case _:
            raise ValueError(
                "EngineStateError: FIRE_BET payout "
                f"requested with {points_hit} distinct "
                "points; expected 4, 5, or 6."
            )




#=================================================
# CONTRACT RULES -> None
#=================================================

def no_contract(
    wager: Wager,
) -> None:
    pass


def pass_line_contract(
        wager: Wager,
) -> None:

    if wager.game.point is None:
        wager.contract_max = None
        wager.contract_min = None
    
    else:
        wager.contract_min = max(
            wager.contract_min or 0,
            wager.value,
        )

        wager.contract_max = (
            None
            if wager.game.settings.allow_put_bets
            else wager.value
        )


def dont_pass_contract(
        wager: Wager,
) -> None:

    wager.contract_min = None

    if wager.game.point is None:
        wager.contract_max = None
    else:
        wager.contract_max = wager.value


def come_contract(
        wager: Wager,
) -> None:

    if wager.target is None:
        wager.contract_max = None
        wager.contract_min = None
    
    else:
        wager.contract_min = max(
            wager.contract_min or 0,
            wager.value,
        )

        wager.contract_max = (
            None
            if wager.game.settings.allow_put_bets
            else wager.value
        )
        

def dont_come_contract(
        wager: Wager,
) -> None:

    wager.contract_min = None
    
    if wager.target is None:
        wager.contract_max = None
    else:
        wager.contract_max = wager.value


def put_contract(
        wager: Wager,
) -> None:

    wager.contract_min = wager.value


def strict_contract(
    wager: Wager,
) -> None:
    """Locks wager into contract after first roll."""

    if wager.contract_max is None:
        wager.contract_max = wager.value

    if wager.contract_min is None:
        wager.contract_min = wager.value



#EOF