import pytest

from engine import wager_definitions as defs
from engine import constants as const
from engine.game import Game
from engine.player import Player
from engine.wager import Wager
from engine.enums import Resolution, WagerType
from engine.exceptions import GameRuleViolation


@pytest.fixture
def dont_pass_game(game_setup) -> tuple[Game, Player, Wager]:
    game, player = game_setup

    wager = Wager(
        definition=defs.DONT_PASS,
        player=player,
        game=game,
        value=25,
    )

    game.place_wager(wager)

    return game, player, wager


#=======================
#DEFINITION TEST
#=======================

def test_dont_pass_definition():
    wager_def = defs.DONT_PASS
    
    assert wager_def.wager_type is WagerType.DONT_PASS
    assert wager_def.name == "Don't Pass"
    assert wager_def.remove_after_win is False
    assert wager_def.can_turn_off is False



#=======================
#PLACEMENT TESTS
#=======================

def test_dont_pass_error_if_placed_with_target(game_setup):
    game, player = game_setup
    
    wager = Wager(
        definition=defs.DONT_PASS,
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


def test_dont_pass_placement_successful_on_comeout(game_setup):
    game, player = game_setup

    wager = Wager(
        definition=defs.DONT_PASS,
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


def test_dont_pass_placement_rejected_on_point_roll(game_setup):

    game, player = game_setup
    game.roll(5)

    wager = Wager(
        definition=defs.DONT_PASS,
        player=player,
        game=game,
        value=25,
    )

    assert player.bankroll == 1500
    assert game.wagers == ()
    with pytest.raises(GameRuleViolation):
        game.place_wager(wager)
    
    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_dont_pass_duplicate_rejection(dont_pass_game):
    game, player, wager = dont_pass_game

    [first_wager] = game.wagers
    wager_type = first_wager.definition.wager_type
    assert wager_type is WagerType.DONT_PASS
    assert wager.player is player

    duplicate_wager = Wager(
        definition=defs.DONT_PASS,
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


def test_multiple_players_dont_trigger_duplicate_error(dont_pass_game):
    game, player, wager = dont_pass_game
    player2 = game.add_player()

    player2_wager = Wager(
        definition=defs.DONT_PASS,
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

def test_dont_pass_take_down_successful_on_comeout(dont_pass_game):
    game, player, wager = dont_pass_game
    assert wager in game.wagers
    assert player.bankroll == 1475

    game.take_down_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_dont_pass_take_down_successful_after_stay_up(dont_pass_game):
    game, player, wager = dont_pass_game
    assert wager in game.wagers
    assert player.bankroll == 1475

    game.roll(6)
    assert game.point == 6

    game.roll(7)
    assert game.point is None
    assert wager in game.wagers
    assert player.bankroll == 1500

    game.take_down_wager(wager)
    assert player.bankroll == 1525
    assert wager not in game.wagers
    assert wager not in player.get_wagers()


def test_dont_pass_take_down_successful_on_point_roll(dont_pass_game):
    game, player, wager = dont_pass_game
    assert wager in game.wagers
    assert player.bankroll == 1475

    game.roll(6)
    assert game.point == 6

    game.take_down_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_dont_pass_cannot_be_turned_off(dont_pass_game):
    game, player, wager = dont_pass_game

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
            (2, Resolution.WIN),
            (3, Resolution.WIN),
            (4, Resolution.NONE),
            (5, Resolution.NONE),
            (6, Resolution.NONE),
            (7, Resolution.LOSE),
            (8, Resolution.NONE),
            (9, Resolution.NONE),
            (10, Resolution.NONE),
            (11, Resolution.LOSE),
            (12, Resolution.PUSH),
        ]
        
)
def test_dont_pass_comeout_resolutions(
    dont_pass_game,
    roll_sum,
    outcome,
):
    game, *_ = dont_pass_game
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
            (6, Resolution.LOSE),
            (7, Resolution.WIN),
            (8, Resolution.NONE),
            (9, Resolution.NONE),
            (10, Resolution.NONE),
            (11, Resolution.NONE),
            (12, Resolution.NONE),
        ]
        
)
def test_dont_pass_all_resolutions_for_single_point(
    dont_pass_game,
    roll_sum,
    outcome,
):
    game, *_ = dont_pass_game
    game.roll(6)
    assert game.point == 6

    [result] = game.roll(roll_sum).wager_results
    
    assert result.resolution is outcome


@pytest.mark.parametrize(
        "point",
        const.BOX_NUMS
)
def test_dont_pass_loses_on_all_points(
    dont_pass_game,
    point,
):
    game, _, wager = dont_pass_game
    
    game.roll(point)
    assert game.point == point

    [result] = game.roll(point).wager_results
    
    assert result.resolution is Resolution.LOSE
    assert game.point is None
    assert wager not in game.wagers


@pytest.mark.parametrize(
        "point",
        const.BOX_NUMS
)
def test_dont_pass_all_points_win_on_7(
    dont_pass_game,
    point,
):
    game, *_ = dont_pass_game

    game.roll(point)
    assert game.point == point

    [result] = game.roll(7).wager_results
    
    assert result.resolution is Resolution.WIN


def test_dont_pass_multiple_wins_without_rebooking(
    dont_pass_game
):
    game, player, wager = dont_pass_game

    [result] = game.roll(2).wager_results
    assert result.resolution is Resolution.WIN
    assert player.bankroll == 1500

    [result] = game.roll(3).wager_results
    assert result.resolution is Resolution.WIN
    assert player.bankroll == 1525

    game.roll(6)

    [result] = game.roll(7).wager_results
    assert result.resolution is Resolution.WIN
    assert player.bankroll == 1550

    assert wager in game.wagers
    assert wager.value == 25
    assert wager.contract_min is None
    assert wager.contract_max is None



#=======================
# PAYOUT TESTS
#=======================

@pytest.mark.parametrize(
    "roll",
    [2, 3, 4, 5, 6, 8, 9, 10]
)
def test_dont_pass_pays_even_money(
    dont_pass_game,
    roll,
):
    game, player, _ = dont_pass_game

    if roll not in (2, 3):
        game.roll(roll)
        [result] = game.roll(7).wager_results

    else:
        [result] = game.roll(roll).wager_results

    assert result.resolution is Resolution.WIN
    assert result.profit == 25
    assert player.bankroll == 1500



#=========================
# WAGER PERSISTENCE TESTS
#=========================

@pytest.mark.parametrize(
    "roll",
    [2, 3, 4, 5, 6, 8, 9, 10],
)
def test_dont_pass_stays_up_after_win(
    dont_pass_game,
    roll,
):
    game, player, wager = dont_pass_game
    
    if roll not in (2,3):
        game.roll(roll)
        [result] = game.roll(7).wager_results
    else:
        [result] = game.roll(roll).wager_results
    
    assert result.resolution is Resolution.WIN
    assert wager in game.wagers
    assert wager.value == 25
    assert game.point is None
    assert player.bankroll == 1500


def test_dont_pass_stays_up_after_push(dont_pass_game):
    game, player, wager = dont_pass_game

    [result] = game.roll(12).wager_results
    
    assert result.resolution is Resolution.PUSH
    assert wager in game.wagers
    assert wager.value == 25
    assert game.point is None
    assert player.bankroll == 1475


@pytest.mark.parametrize(
    "roll",
    [7, 11, 4, 5, 6, 8, 9, 10]
)
def test_dont_pass_removed_after_loss(
    dont_pass_game,
    roll,
):
    game, player, wager = dont_pass_game


    if roll not in (7,11):
        game.roll(roll)

    [result] = game.roll(roll).wager_results

    assert result.resolution is Resolution.LOSE
    assert wager not in game.wagers
    assert wager not in player.get_wagers()
    assert player.bankroll == 1475
    assert game.point is None



#=========================
# CONTRACT TESTS
#=========================

def test_dont_pass_contract_sets_with_point(dont_pass_game):
    game, player, wager = dont_pass_game
    
    assert game.point is None
    assert wager.contract_max is None
    assert wager.contract_min is None

    game.increase_wager(wager, 1)
    assert wager.value == 26

    game.decrease_wager(wager, 1)
    assert wager.value == 25
    
    game.roll(6)

    assert wager.contract_max == 25
    assert wager.contract_min is None

    game.roll(8)

    assert wager.contract_max == 25
    assert wager.contract_min is None

    with pytest.raises(
        GameRuleViolation,
    ):
        game.increase_wager(wager, 1)

    game.decrease_wager(wager, 1)
    
    assert wager.value == 24
    assert player.bankroll == 1476


def test_dont_pass_contract_resets_on_comeout(dont_pass_game):
    game, player, wager = dont_pass_game
    
    game.roll(6)
    assert wager.contract_min is None
    assert wager.contract_max == 25

    game.roll(7)

    assert wager.contract_min is None
    assert wager.contract_max is None
    assert game.point is None

    game.increase_wager(wager, 10)
    assert wager.value == 35
    assert player.bankroll == 1490

    game.decrease_wager(wager, 10)
    assert wager.value == 25
    assert player.bankroll == 1500


def test_dont_pass_contract_decreases_with_value_after_roll(dont_pass_game):
    game, _, wager = dont_pass_game

    assert wager.value ==  25
    assert wager.contract_max is None
    assert wager.contract_min is None
    
    game.roll(4)

    assert wager.value ==  25
    assert wager.contract_max == 25
    assert wager.contract_min is None

    game.decrease_wager(wager, 10)

    assert wager.value ==  15
    assert wager.contract_max == 25
    assert wager.contract_min is None

    game.roll(5)
    
    assert wager.value ==  15
    assert wager.contract_min is None
    assert wager.contract_max == 15

    with pytest.raises(GameRuleViolation):
        game.increase_wager(wager, 1)

    assert wager.value == 15


def test_dont_pass_can_restore_value_before_next_roll(
    dont_pass_game
):
    game, player, wager = dont_pass_game

    game.roll(6)

    assert wager.contract_max == 25

    game.decrease_wager(wager, 10)

    assert wager.value == 15
    assert wager.contract_max == 25

    game.increase_wager(wager, 10)

    assert wager.value == 25
    assert player.bankroll == 1475

    game.roll(8)

    assert wager.contract_max == 25


#=========================
# LIFECYCLE TEST
#=========================

def test_dont_pass_lifecycle(game_setup):
    game, player = game_setup

    wager = Wager(
        definition=defs.DONT_PASS,
        player=player,
        game=game,
        value=25,
    )

    assert player.bankroll == 1500

    #Place Wager
    game.place_wager(wager)
    assert wager in game.wagers
    assert wager in player.get_wagers()
    assert player.bankroll == 1475

    # Increase Wager before locked in
    game.increase_wager(wager, 10)
    assert wager.value == 35
    assert player.bankroll == 1465

    # Natrual Win, bet stays up
    [result] = game.roll(3).wager_results
    assert result.resolution is Resolution.WIN
    assert result.profit == 35
    assert player.bankroll == 1500
    assert wager in game.wagers
    assert wager in player.get_wagers()

    # Push, bet stays up
    [result] = game.roll(12).wager_results
    assert result.resolution is Resolution.PUSH
    assert result.profit == 0
    assert player.bankroll == 1500
    assert wager in game.wagers
    assert wager in player.get_wagers()

    # Establish a point
    assert game.point is None
    [result] = game.roll(5).wager_results
    assert result.resolution is Resolution.NONE
    assert result.profit == 0
    assert game.point == 5
    assert wager.contract_min is None
    assert wager.contract_max == 35

    # Contract prevents increase
    with pytest.raises(GameRuleViolation):
        game.increase_wager(wager, 10)
    assert wager.value == 35
    assert player.bankroll == 1500

    # Decrease wager allowed per contract
    game.decrease_wager(wager, 10)
    assert wager.value == 25
    assert wager.contract_min is None
    assert wager.contract_max == 35
    assert player.bankroll == 1510
    
    # Non-resolving roll
    [result] = game.roll(12).wager_results
    assert result.resolution is Resolution.NONE
    assert result.profit == 0
    assert game.point == 5
    assert wager in game.wagers
    assert player.bankroll == 1510

    # Contract max resets to 25
    assert wager.contract_min is None
    assert wager.contract_max == 25
    assert player.bankroll == 1510

    # Seven winner 
    [result] = game.roll(7).wager_results
    assert result.resolution is Resolution.WIN
    assert result.profit == 25
    assert player.bankroll == 1535
    assert wager in game.wagers
    assert wager in player.get_wagers()
    assert game.point is None

    # Contract release
    assert wager.contract_min is None
    assert wager.contract_max is None

    # Comeout loser
    [result] = game.roll(7).wager_results
    assert result.resolution is Resolution.LOSE
    assert result.profit == 0
    assert player.bankroll == 1535

    # Game back to initial state
    assert wager not in game.wagers
    assert wager not in player.get_wagers()
    assert game.point is None