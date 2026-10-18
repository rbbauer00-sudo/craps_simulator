import pytest
from dataclasses import replace

from engine import wager_definitions as defs
from engine import constants as const
from engine.game import Game
from engine.player import Player
from engine.wager import Wager
from engine.enums import Resolution, WagerType
from engine.exceptions import GameRuleViolation


@pytest.fixture
def passline_game(game_setup) -> tuple[Game, Player, Wager]:
    game, player = game_setup

    wager = Wager(
        definition=defs.PASS_LINE,
        player=player,
        game=game,
        value=25,
    )

    game.place_wager(wager)

    return game, player, wager



#=======================
#DEFINITION TEST
#=======================

def test_passline_definition():
    wager_def = defs.PASS_LINE

    assert wager_def.wager_type is WagerType.PASS_LINE
    assert wager_def.name == "Pass Line"
    assert wager_def.remove_after_win is False
    assert wager_def.can_turn_off is False



#=======================
#PLACEMENT TESTS
#=======================

def test_passline_error_if_placed_with_target(game_setup):
    game, player = game_setup
    
    wager = Wager(
        definition=defs.PASS_LINE,
        player=player,
        game=game,
        value=25,
        target=5
    )
    
    assert player.bankroll == 1500
    assert wager not in game.wagers
    assert game.point is None

    with pytest.raises(ValueError):
        game.place_wager(wager)

    assert player.bankroll == 1500
    assert wager not in game.wagers


def test_passline_placement_successful_on_comeout(game_setup):
    game, player = game_setup

    wager = Wager(
        definition=defs.PASS_LINE,
        player=player,
        game=game,
        value=25,
    )
    
    assert player.bankroll == 1500
    assert wager not in game.wagers
    assert game.point is None

    game.place_wager(wager)

    assert player.bankroll == 1475
    assert wager in game.wagers


def test_passline_placement_rejected_on_point_roll(game_setup):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        allow_put_bets=False, 
    )
    game._settings = new_settings
    game.roll(5)

    wager = Wager(
        definition=defs.PASS_LINE,
        player=player,
        game=game,
        value=25,
    )

    assert player.bankroll == 1500
    assert game.wagers == ()
    assert game.point == 5

    with pytest.raises(GameRuleViolation):
        game.place_wager(wager)

    assert player.bankroll == 1500
    assert wager not in game.wagers


def test_passline_duplicate_rejection(passline_game):
    game, player, wager = passline_game

    [first_wager] = game.wagers
    wager_type = first_wager.definition.wager_type
    assert wager_type is WagerType.PASS_LINE
    assert wager.player is player

    duplicate_wager = Wager(
        definition=defs.PASS_LINE,
        player=player,
        game=game,
        value=25
    )

    with pytest.raises(
        GameRuleViolation
    ):
        game.place_wager(duplicate_wager)

    assert wager in game.wagers
    assert duplicate_wager not in game.wagers
    assert player.bankroll == 1475


def test_multiple_players_dont_trigger_duplicate_error(passline_game):

    game, player, wager = passline_game
    player2 = game.add_player()

    player2_wager = Wager(
        definition=defs.PASS_LINE,
        player=player2,
        game=game,
        value=25
    )

    game.place_wager(player2_wager)

    assert wager in game.wagers
    assert player2_wager in game.wagers

    assert player.bankroll == 1475
    assert player2.bankroll == 1475



#=======================
# WAGER ADJUSTMENT TESTS
#=======================

def test_passline_take_down_successful_on_comeout(passline_game):
    game, player, wager = passline_game
    assert wager in game.wagers
    assert player.bankroll == 1475

    game.take_down_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_passline_take_down_successful_after_stay_up(passline_game):
    game, player, wager = passline_game
    assert wager in game.wagers
    assert player.bankroll == 1475

    game.roll(6)
    assert game.point == 6

    game.roll(6)
    assert game.point is None
    assert wager in game.wagers
    assert player.bankroll == 1500

    game.take_down_wager(wager)
    assert player.bankroll == 1525


def test_passline_take_down_rejected_on_point_roll(passline_game):
    game, player, wager = passline_game
    assert wager in game.wagers
    assert player.bankroll == 1475

    game.roll(6)
    assert game.point == 6

    with pytest.raises(GameRuleViolation):
        game.take_down_wager(wager)
    assert wager in game.wagers
    assert player.bankroll == 1475


def test_passline_cannot_be_turned_off(passline_game):
    game, player, wager = passline_game

    assert wager in game.wagers
    assert player.bankroll == 1475

    with pytest.raises(GameRuleViolation):
        game.set_wager_working_status(wager, False)

    assert wager.is_working is True
    assert wager in game.wagers
    assert player.bankroll == 1475
    
    game.roll(6)
    assert game.point == 6

    with pytest.raises(GameRuleViolation):
        game.set_wager_working_status(wager, False)

    assert wager.is_working is True
    assert wager in game.wagers
    assert player.bankroll == 1475



#=======================
# RESOLUTION TESTS
#=======================

@pytest.mark.parametrize(
        "roll_sum, outcome",
        [
            (2, Resolution.LOSE),
            (3, Resolution.LOSE),
            (4, Resolution.NONE),
            (5, Resolution.NONE),
            (6, Resolution.NONE),
            (7, Resolution.WIN),
            (8, Resolution.NONE),
            (9, Resolution.NONE),
            (10, Resolution.NONE),
            (11, Resolution.WIN),
            (12, Resolution.LOSE),
        ]
        
)
def test_pass_line_comeout_resolutions(
    passline_game,
    roll_sum,
    outcome,
):
    game, *_ = passline_game
    assert game.point is None

    [result] = game.roll(roll_sum).wager_results
    
    assert result.resolution is outcome


@pytest.mark.parametrize(
        "roll_sum, outcome",
        [
            (2, Resolution.NONE),
            (3, Resolution.NONE),
            (4, Resolution.NONE),
            (5, Resolution.NONE),
            (6, Resolution.WIN),
            (7, Resolution.LOSE),
            (8, Resolution.NONE),
            (9, Resolution.NONE),
            (10, Resolution.NONE),
            (11, Resolution.NONE),
            (12, Resolution.NONE),
        ]
        
)
def test_pass_line_all_resolutions_for_single_point(
    passline_game,
    roll_sum,
    outcome,
):
    game, *_ = passline_game
    game.roll(6)
    assert game.point == 6

    [result] = game.roll(roll_sum).wager_results
    
    assert result.resolution is outcome


@pytest.mark.parametrize(
        "point",
        const.BOX_NUMS
)
def test_pass_line_wins_on_all_points(
    passline_game,
    point,
):
    game, _, wager = passline_game

    game.roll(point)
    assert game.point == point

    [result] = game.roll(point).wager_results
    assert result.resolution is Resolution.WIN

    assert game.point is None
    assert wager in game.wagers


@pytest.mark.parametrize(
        "point",
        const.BOX_NUMS
)
def test_pass_line_all_points_lose_on_7(
    passline_game,
    point,
):
    game, *_ = passline_game

    game.roll(point)
    assert game.point == point
    
    [result] = game.roll(7).wager_results
    
    assert result.resolution is Resolution.LOSE



#=======================
# PAYOUT TESTS
#=======================

@pytest.mark.parametrize(
    "roll",
    [7, 11, 4, 5, 6, 8, 9, 10]
)
def test_passline_pays_even_money(
    passline_game,
    roll,
):
    game, player, _ = passline_game

    if roll not in (7, 11):
        game.roll(roll)

    [result] = game.roll(roll).wager_results

    assert result.resolution is Resolution.WIN
    assert result.profit == 25
    assert player.bankroll == 1500



#=========================
# WAGER PERSISTENCE TESTS
#=========================

@pytest.mark.parametrize(
    "roll",
    [7, 11, 4, 5, 6, 8, 9, 10],
)
def test_pass_line_stays_up_after_win(
    passline_game,
    roll,
):
    game, player, wager = passline_game
    
    if roll not in (7,11):
        game.roll(roll)
    
    [result] = game.roll(roll).wager_results
    
    assert result.resolution is Resolution.WIN
    assert wager in game.wagers
    assert wager.value == 25
    assert game.point is None
    assert player.bankroll == 1500


@pytest.mark.parametrize(
    "roll",
    [2, 3, 12, 4, 5, 6, 8, 9, 10]
)
def test_pass_line_removed_after_loss(
    passline_game,
    roll,
):
    game, player, wager = passline_game

    game.roll(roll)

    if roll not in (2, 3, 12):
        assert wager in game.wagers
        game.roll(7)

    assert wager not in game.wagers
    assert wager not in player.get_wagers()
    assert player.bankroll == 1475
    assert game.point is None



#=========================
# CONTRACT TESTS
#=========================

def test_pass_line_contract_sets_with_point(passline_game):
    game, player, wager = passline_game
    new_settings = replace(
        game.settings,
        allow_put_bets=False, 
    )
    game._settings = new_settings
    
    assert game.point is None
    assert wager.contract_max is None
    assert wager.contract_min is None

    game.increase_wager(wager, 1)
    assert wager.value == 26

    game.decrease_wager(wager, 1)
    assert wager.value == 25
    
    game.roll(6)

    assert wager.contract_max == 25
    assert wager.contract_min == 25

    game.roll(8)

    assert wager.contract_min == 25
    assert wager.contract_max == 25

    with pytest.raises(
        GameRuleViolation,
    ):
        game.increase_wager(wager, 1)

    with pytest.raises(
            GameRuleViolation,
        ):
            game.decrease_wager(wager, 1)

    assert wager.value == 25
    assert player.bankroll == 1475


def test_pass_line_contract_resets_on_comeout(passline_game):
    game, player, wager = passline_game
    new_settings = replace(
        game.settings,
        allow_put_bets=False, 
    )
    game._settings = new_settings
    
    game.roll(6)
    assert wager.contract_min == 25
    assert wager.contract_max == 25

    game.roll(6)

    assert wager.contract_min is None
    assert wager.contract_max is None
    assert game.point is None

    game.increase_wager(wager, 10)
    assert wager.value == 35
    assert player.bankroll == 1490

    game.decrease_wager(wager, 10)
    assert wager.value == 25
    assert player.bankroll == 1500




#=======================
# PUT PASS LINE TESTS
#=======================

@pytest.mark.parametrize("point", sorted(const.BOX_NUMS))
@pytest.mark.parametrize("allowed", [False, True], ids=["disabled", "enabled"])
def test_put_pass_line_direct_placement(game_setup, point, allowed):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        allow_put_bets=allowed, 
    )
    game._settings = new_settings
    game.roll(point)  # Establish the table point without a Pass Line wager.

    wager = Wager(
        definition=defs.PASS_LINE, 
        player=player, 
        game=game,
        value=25,
    )

    if allowed:
        game.place_wager(wager)
        assert wager in game.wagers
        assert player.bankroll == 1475
        assert wager.contract_min is None  # Contracts refresh on rolls.
        assert wager.contract_max is None
    else:
        with pytest.raises(GameRuleViolation):
            game.place_wager(wager)
        assert wager not in game.wagers
        assert player.bankroll == 1500


@pytest.mark.parametrize("winning", [True, False], ids=["win", "lose"])
def test_put_pass_line_direct_placement_resolves(game_setup, winning):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        allow_put_bets=True, 
    )
    game._settings = new_settings
    game.roll(6)
    wager = Wager(
        definition=defs.PASS_LINE, 
        player=player,
        game=game, 
        value=25,
    )

    game.place_wager(wager)

    [result] = game.roll(6 if winning else 7).wager_results
    assert result.resolution is (Resolution.WIN if winning else Resolution.LOSE)
    assert result.profit == (25 if winning else 0)
    assert (wager in game.wagers) is winning  # Pass Line stays after win.
    assert player.bankroll == (1500 if winning else 1475)


def test_put_pass_line_increase_and_contract_ratchet(passline_game):
    game, player, wager = passline_game
    new_settings = replace(
        game.settings,
        allow_put_bets=True, 
    )
    game._settings = new_settings
    game.roll(6)

    assert wager.contract_min == 25
    assert wager.contract_max is None

    game.increase_wager(wager, 50)
    assert wager.value == 75
    assert wager.contract_min == 25
    assert player.bankroll == 1425

    # The additional money remains removable until the next roll.
    game.decrease_wager(wager, 30)
    assert wager.value == 45
    assert wager.contract_min == 25
    assert player.bankroll == 1455

    game.roll(8)  # Point still 6; lock the new amount.
    assert wager.value == 45
    assert wager.contract_min == 45
    assert wager.contract_max is None

    with pytest.raises(GameRuleViolation):
        game.decrease_wager(wager, 1)
    assert wager.value == 45
    assert player.bankroll == 1455

    game.increase_wager(wager, 5)
    assert wager.value == 50
    assert wager.contract_min == 45
    assert player.bankroll == 1450

    [result] = game.roll(6).wager_results
    assert result.resolution is Resolution.WIN
    assert result.profit == 50
    assert player.bankroll == 1500
    assert wager in game.wagers
    assert wager.contract_min is None
    assert wager.contract_max is None


def test_put_pass_line_increase_loses_full_amount(passline_game):
    game, player, wager = passline_game
    new_settings = replace(
        game.settings,
        allow_put_bets=True, 
    )
    game._settings = new_settings
    game.roll(6)
    game.increase_wager(wager, 50)

    [result] = game.roll(7).wager_results
    assert result.resolution is Resolution.LOSE
    assert result.profit == 0
    assert wager not in game.wagers
    assert player.bankroll == 1425


def test_put_pass_line_disabled_increase_preserves_funds(passline_game):
    game, player, wager = passline_game
    new_settings = replace(
        game.settings,
        allow_put_bets=False, 
    )
    game._settings = new_settings
    game.roll(6)

    assert wager.contract_min == 25
    assert wager.contract_max == 25
    with pytest.raises(GameRuleViolation):
        game.increase_wager(wager, 50)
    assert wager.value == 25
    assert player.bankroll == 1475


def test_put_pass_line_does_not_allow_duplicate_wager(passline_game):
    game, player, wager = passline_game
    new_settings = replace(
        game.settings,
        allow_put_bets=True, 
    )
    game._settings = new_settings
    game.roll(6)

    duplicate = Wager(
        definition=defs.PASS_LINE, 
        player=player,
        game=game, 
        value=25,
    )

    with pytest.raises(GameRuleViolation):
        game.place_wager(duplicate)
    assert game.wagers == (wager,)
    assert player.bankroll == 1475


#=========================
# LIFECYCLE TEST
#=========================

def test_passline_lifecycle(game_setup):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        allow_put_bets=False, 
    )
    game._settings = new_settings

    wager = Wager(
        definition=defs.PASS_LINE,
        player=player,
        game=game,
        value=25,
    )

    assert player.bankroll == 1500

    # Place Wager
    game.place_wager(wager)    
    assert wager in game.wagers
    assert wager in player.get_wagers()
    assert player.bankroll == 1475

    # Increase Wager before locked in
    game.increase_wager(wager, 10)
    assert wager.value == 35
    assert player.bankroll == 1465

    # Natrual Win, bet stays up
    [result] = game.roll(11).wager_results
    assert result.resolution is Resolution.WIN
    assert result.profit == 35
    assert player.bankroll == 1500
    assert wager in game.wagers
    assert wager in player.get_wagers()

    # Establish a point
    assert game.point is None
    [result] = game.roll(5).wager_results
    assert result.resolution is Resolution.NONE
    assert result.profit == 0
    assert game.point == 5
    assert wager.contract_min == 35
    assert wager.contract_max == 35

    # Non-resolving roll
    [result] = game.roll(12).wager_results
    assert result.resolution is Resolution.NONE
    assert result.profit == 0
    assert game.point == 5
    assert wager in game.wagers
    assert wager.contract_min == 35
    assert wager.contract_max == 35
    assert player.bankroll == 1500

    # Contract now prevents adjustment
    with pytest.raises(GameRuleViolation):
        game.increase_wager(wager, 10)
    assert wager.value == 35

    with pytest.raises(GameRuleViolation):
        game.decrease_wager(wager, 10)
    
    assert wager.value == 35
    assert player.bankroll == 1500

    # Point winner 
    [result] = game.roll(5).wager_results
    assert result.resolution is Resolution.WIN
    assert result.profit == 35
    assert player.bankroll == 1535
    assert wager in game.wagers
    assert wager in player.get_wagers()
    assert game.point is None

    # Contract release
    assert wager.contract_min is None
    assert wager.contract_max is None

    # Comeout loser
    [result] = game.roll(3).wager_results
    assert result.resolution is Resolution.LOSE
    assert result.profit == 0
    assert player.bankroll == 1535

    # Game back to initial state
    assert wager not in game.wagers
    assert wager not in player.get_wagers()
    assert game.point is None




    