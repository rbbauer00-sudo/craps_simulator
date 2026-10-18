import pytest
from dataclasses import replace

from craps_engine import wager_definitions as defs
from craps_engine import constants as const
from craps_engine.game import Game
from craps_engine.player import Player
from craps_engine.wager import Wager
from craps_engine.enums import Resolution, WagerType
from craps_engine.exceptions import GameRuleViolation


@pytest.fixture
def field_bet_game(game_setup) -> tuple[Game, Player, Wager]:
    game, player = game_setup

    wager = Wager(
        definition=defs.FIELD,
        player=player,
        game=game,
        value=25,
    )
    game.place_wager(wager)
    return game, player, wager



#=======================
#DEFINITION TEST
#=======================

def test_wager_definition():
    wager_def = defs.FIELD
    
    assert wager_def.wager_type is WagerType.FIELD
    assert wager_def.name == "Field"
    assert wager_def.remove_after_win is False
    assert wager_def.can_turn_off is False



#=======================
#PLACEMENT TESTS
#=======================

def test_field_bet_error_if_placed_with_target(game_setup):
    game, player = game_setup
    
    wager = Wager(
        definition=defs.FIELD,
        player=player,
        game=game,
        value=25,
        target=5,
    )
    
    assert player.bankroll == 1500
    assert wager not in game.wagers
    assert game.point is None

    with pytest.raises(ValueError):
        game.place_wager(wager)

    assert player.bankroll == 1500
    assert wager not in game.wagers


@pytest.mark.parametrize(
    "point",
    [None, *const.BOX_NUMS],
)
def test_field_placement_success_regardless_of_point(
    game_setup,
    point,
):
    game, player = game_setup

    if point is not None:
        game.roll(point)

    wager = Wager(
        definition=defs.FIELD,
        player=player,
        game=game,
        value=25,
    )
    
    assert player.bankroll == 1500
    assert wager not in game.wagers
    assert game.point == point

    game.place_wager(wager)

    assert player.bankroll == 1475
    assert wager in game.wagers


def test_field_bet_duplicate_rejection(field_bet_game):
    game, player, wager = field_bet_game

    [first_wager] = game.wagers
    wager_type = first_wager.definition.wager_type
    assert wager_type is WagerType.FIELD
    assert wager.player is player

    duplicate_wager = Wager(
        definition=defs.FIELD,
        player=player,
        game=game,
        value=100,
    )

    with pytest.raises(
        GameRuleViolation
    ):
        game.place_wager(duplicate_wager)

    assert wager in game.wagers
    assert duplicate_wager not in game.wagers
    assert player.bankroll == 1475


def test_multiple_players_dont_trigger_duplicate_error(field_bet_game):

    game, player, wager = field_bet_game
    player2 = game.add_player()

    player2_wager = Wager(
        definition=defs.FIELD,
        player=player2,
        game=game,
        value=25,
    )

    game.place_wager(player2_wager)

    assert wager in game.wagers
    assert player2_wager in game.wagers

    assert player.bankroll == 1475
    assert player2.bankroll == 1475



#=======================
# WAGER ADJUSTMENT TESTS
#=======================

@pytest.mark.parametrize(
    "roll",
    const.FIELD_NUMS,
)
def test_field_takedown_success_after_stay_up(
    field_bet_game,
    roll,
):
    game, player, wager = field_bet_game

    [result] = game.roll(roll).wager_results
    assert wager in game.wagers

    game.take_down_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500 + result.profit

def test_field_bet_cannot_be_turned_off(field_bet_game):
    game, player, wager = field_bet_game

    assert wager in game.wagers
    assert player.bankroll == 1475

    with pytest.raises(GameRuleViolation):
        game.set_wager_working_status(wager, False)

    assert wager.is_working is True
    assert wager in game.wagers
    assert player.bankroll == 1475
    


#=======================
# RESOLUTION TESTS
#=======================

@pytest.mark.parametrize(
    "total, expected",
    [
        (2, Resolution.WIN),
        (3, Resolution.WIN),
        (4, Resolution.WIN),
        (5, Resolution.LOSE),
        (6, Resolution.LOSE),
        (7, Resolution.LOSE),
        (8, Resolution.LOSE),
        (9, Resolution.WIN),
        (10, Resolution.WIN),
        (11, Resolution.WIN),
        (12, Resolution.WIN),
    ],
)
def test_field_bet_resolutions(
    field_bet_game,
    total,
    expected,
):
    game, _, wager = field_bet_game

    [result] = game.roll(total).wager_results

    assert result.resolution is expected


def test_field_bet_resolves_on_comeout(game_setup):
    game, player = game_setup

    wager = Wager(
        definition=defs.FIELD,
        player=player,
        game=game,
        value=25,
    )

    game.place_wager(wager)

    assert game.point is None

    [result] = game.roll(7).wager_results

    assert result.resolution is Resolution.LOSE
    assert wager not in game.wagers
    assert player.bankroll == 1475
    assert game.point is None



#=======================
# PAYOUT TESTS
#=======================

@pytest.mark.parametrize(
    "roll, expected_profit",
    [
        (2,50),
        (3,25),
        (4,25),
        (5,0),
        (6,0),
        (7,0),
        (8,0),
        (9,25),
        (10,25),
        (11,25),
    ],
)
def test_field_bet_fixed_payouts(
    field_bet_game,
    roll,
    expected_profit,
):
    game, *_= field_bet_game
    
    [result] = game.roll(roll).wager_results

    assert result.profit == expected_profit


@pytest.mark.parametrize(
    "game_setting, expected_profit",
    [
        (True,75),
        (False,50),
    ],
    ids=["3x-75", "2x-50"]
)
def test_field_bet_triple_12_rule(
    field_bet_game,
    game_setting,
    expected_profit,
):
    game, *_ = field_bet_game
    new_settings = replace(
        game.settings,
        field_3x_on_12=game_setting,
    )
        
    game._settings = new_settings
    
    [result] = game.roll(12).wager_results

    assert result.profit == expected_profit



#=========================
# WAGER PERSISTENCE TESTS
#=========================

@pytest.mark.parametrize(
        "roll",
        const.FIELD_NUMS,
)
def test_field_bet_stays_up_after_win(
    field_bet_game,
    roll,
):
    game, player, wager = field_bet_game
    
    [result] = game.roll(roll).wager_results
    
    assert result.resolution is Resolution.WIN
    assert wager in game.wagers
    assert wager in player.get_wagers()
    expected_bankroll = result.profit + 1475
    assert player.bankroll == expected_bankroll


@pytest.mark.parametrize(
        "roll",
        [5, 6, 7, 8],
)
def test_field_bet_removed_after_loss(
    field_bet_game,
    roll,
):
    game, player, wager = field_bet_game
    
    [result] = game.roll(roll).wager_results
    
    assert result.resolution is Resolution.LOSE
    assert wager not in game.wagers
    assert wager not in player.get_wagers()
    assert player.bankroll == 1475



#=========================
# CONTRACT TESTS
#=========================

@pytest.mark.parametrize(
        "roll",
        const.ALL_NUMS,
)
def test_field_bet_never_has_contract(
    field_bet_game,
    roll,
):
    game, _, wager = field_bet_game

    game.roll(roll)

    assert wager.contract_max is None
    assert wager.contract_min is None



#=========================
# LIFECYCLE TEST
#=========================

def test_field_bet_lifecycle(game_setup):
    game, player = game_setup

    wager = Wager(
        definition=defs.FIELD,
        player=player,
        game=game,
        value=25,
    )

    assert player.bankroll == 1500

    game.place_wager(wager)

    assert player.bankroll == 1475

    assert wager in game.wagers
    assert wager in player.get_wagers()

    [result] = game.roll(12).wager_results
    
    assert result.resolution is Resolution.WIN
    assert result.profit == 75
    
    assert player.bankroll == 1550
    assert wager in game.wagers
    assert wager in player.get_wagers()
    
    [result] = game.roll(5).wager_results
    
    assert result.resolution is Resolution.LOSE
    assert result.profit == 0
    
    assert player.bankroll == 1550
    assert wager not in game.wagers
    assert wager not in player.get_wagers()

