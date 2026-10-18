from . import wager_rules as rules
from . import constants as const
from .wager import WagerDefinition 
from .enums  import WagerType


# =================================================
# PROP BETS
# =================================================

ANY_CRAPS = WagerDefinition(
    wager_type=WagerType.ANY_CRAPS,
    name="Any Craps",
    placement_rule=rules.validate_prop_placement,
    resolution_rule=rules.simple_resolution(
        winning_totals={2, 3, 12},
    ),
    payout_rule=rules.fixed_multiple_payout(7),
)


ANY_SEVEN = WagerDefinition(
    wager_type=WagerType.ANY_SEVEN,
    name="Any Seven",
    placement_rule=rules.validate_prop_placement,
    resolution_rule=rules.simple_resolution(
        winning_totals={7,},
    ),
    payout_rule=rules.fixed_multiple_payout(4),
)


YO_LEVEN = WagerDefinition(
    wager_type=WagerType.YO_LEVEN,
    name='Yo-Leven',
    placement_rule=rules.validate_prop_placement,
    resolution_rule=rules.simple_resolution(
        winning_totals={11,},
    ),
    payout_rule=rules.fixed_multiple_payout(15),
    )


MIDNIGHT = WagerDefinition(
    wager_type=WagerType.MIDNIGHT,
    name='Midnight',
    placement_rule=rules.validate_prop_placement,
    resolution_rule=rules.simple_resolution(
        winning_totals={12,}
    ),
    payout_rule=rules.fixed_multiple_payout(30),
)


ACE_DEUCE = WagerDefinition(
    wager_type=WagerType.ACE_DEUCE,
    name='Ace-Deuce',
    placement_rule=rules.validate_prop_placement,
    resolution_rule=rules.simple_resolution(
        winning_totals={3,}
    ),
    payout_rule=rules.fixed_multiple_payout(15),
)


DEUCE = WagerDefinition(
    wager_type=WagerType.DEUCE,
    name='Deuce',
    placement_rule=rules.validate_prop_placement,
    resolution_rule=rules.simple_resolution(
        winning_totals={2,}
    ),
    payout_rule=rules.fixed_multiple_payout(30),
)



# =================================================
# HARDWAYS / HOPS / FIELD
# =================================================

HARDWAY = WagerDefinition(
    wager_type=WagerType.HARDWAY,
    name='Hard',
    placement_rule=rules.validate_hardway_placement,
    resolution_rule=rules.hardway_resolution,
    payout_rule=rules.hardway_payout,
    can_turn_off=True,
)


HOP_BET = WagerDefinition(
    wager_type=WagerType.HOP,
    name='Hop',
    placement_rule=rules.validate_hop_placement,
    resolution_rule=rules.hop_resolution,
    payout_rule=rules.hop_payout,
)


FIELD = WagerDefinition(
    wager_type=WagerType.FIELD,
    name="Field",
    placement_rule=rules.validate_prop_placement,
    resolution_rule=rules.simple_resolution(
        winning_totals=const.FIELD_NUMS,
    ),
    payout_rule = rules.field_payout,    
)



# =================================================
# LINE BETS
# =================================================

PASS_LINE = WagerDefinition(
    wager_type=WagerType.PASS_LINE,
    name="Pass Line",
    placement_rule=rules.validate_pass_line_placement,
    contract_rule=rules.pass_line_contract,
    resolution_rule=rules.pass_line_resolution,
    payout_rule = rules.even_money_payout,
)


DONT_PASS = WagerDefinition(
    wager_type=WagerType.DONT_PASS,
    name="Don't Pass",
    placement_rule=rules.validate_dont_pass_placement,
    resolution_rule=rules.dont_pass_resolution,
    payout_rule=rules.even_money_payout,
    contract_rule=rules.dont_pass_contract,
)



# =================================================
# COME / DON'T COME
# =================================================

COME = WagerDefinition(
    wager_type=WagerType.COME,
    name="Come",
    placement_rule=rules.validate_come_placement,
    contract_rule=rules.come_contract,
    resolution_rule=rules.come_bet_resolution,
    payout_rule=rules.even_money_payout,
    remove_after_win=True,
)


DONT_COME = WagerDefinition(
    wager_type=WagerType.DONT_COME,
    name="Don't Come",
    placement_rule=rules.validate_dont_come_placement,
    contract_rule=rules.dont_come_contract,
    resolution_rule=rules.dont_come_resolution,
    payout_rule=rules.even_money_payout,
    remove_after_win=True,
)



# =================================================
# ODDS BETS
# =================================================

LINE_ODDS = WagerDefinition(
    wager_type=WagerType.LINE_ODDS,
    name="Line Odds",
    placement_rule=rules.validate_line_odds_placement,
    resolution_rule=rules.line_odds_resolution,
    payout_rule=rules.line_odds_payout,
    can_turn_off=True,
    remove_after_win=True,
)

LAY_ODDS = WagerDefinition(
    wager_type=WagerType.LAY_ODDS,
    name="Lay Odds",
    placement_rule=rules.validate_lay_odds_placement,
    resolution_rule=rules.lay_odds_resolution,
    payout_rule=rules.lay_odds_payout,
    can_turn_off=True,
    remove_after_win=True,
)


# =================================================
# PLACE/LAY BETS
# =================================================

PLACE_BET = WagerDefinition(
    wager_type=WagerType.PLACE_BET,
    name = "Place",
    placement_rule=rules.validate_place_lay_bet_placement,
    resolution_rule=rules.place_bet_resolution,
    payout_rule=rules.place_bet_payout,
    can_turn_off=True,
)


LAY_BET = WagerDefinition(
    wager_type=WagerType.LAY_BET,
    name = "Lay",
    placement_rule=rules.validate_place_lay_bet_placement,
    resolution_rule=rules.lay_bet_resolution,
    payout_rule=rules.lay_bet_payout,
)


# =================================================
# FIRE/ATS BETS
# =================================================

ATS_ALL = WagerDefinition(
    wager_type=WagerType.ATS_ALL,
    name = "ATS All",
    placement_rule=rules.validate_ats_placement,
    contract_rule=rules.strict_contract,
    resolution_rule=rules.ats_resolution,
    payout_rule=rules.fixed_multiple_payout(176),
    remove_after_win=True,
)

ATS_TALL = WagerDefinition(
    wager_type=WagerType.ATS_TALL,
    name = "ATS tall",
    placement_rule=rules.validate_ats_placement,
    contract_rule=rules.strict_contract,
    resolution_rule=rules.ats_resolution,
    payout_rule=rules.fixed_multiple_payout(35),
    remove_after_win=True,
)

ATS_SMALL = WagerDefinition(
    wager_type=WagerType.ATS_SMALL,
    name = "ATS Small",
    placement_rule=rules.validate_ats_placement,
    contract_rule=rules.strict_contract,
    resolution_rule=rules.ats_resolution,
    payout_rule=rules.fixed_multiple_payout(35),
    remove_after_win=True,
)

FIRE_BET = WagerDefinition(
    wager_type=WagerType.FIRE_BET,
    name="Fire Bet",
    placement_rule=rules.validate_fire_bet_placement,
    contract_rule=rules.strict_contract,
    resolution_rule=rules.fire_bet_resolution,
    payout_rule=rules.fire_bet_payout,
    remove_after_win=True,
)
