import pytest
from conftest import get_result
from dataclasses import replace

from craps_engine import wager_definitions as defs
from craps_engine import constants as const
from craps_engine.game import Game
from craps_engine.player import Player
from craps_engine.wager import Wager
from craps_engine.enums import Resolution, WagerType
from craps_engine.exceptions import GameRuleViolation


@pytest.fixture
def dont_come_game(game_setup) -> tuple[Game, Player, Wager]:
    game, player = game_setup

    wager = Wager(
        definition=defs.DONT_COME,
        player=player,
        game=game,
        value=25
    )

    game._point = 6

    game.place_wager(wager)
    
    return game, player, wager



#=======================
#DEFINITION TEST
#=======================

def test_wager_definition():
    wager_def = defs.DONT_COME
    
    assert wager_def.wager_type is WagerType.DONT_COME
    assert wager_def.name == "Don't Come"
    assert wager_def.can_turn_off is False
    assert wager_def.remove_after_win is True



#=======================
#PLACEMENT TESTS
#=======================

def test_dont_come_error_if_placed_with_target(game_setup):
    game, player = game_setup
    
    wager = Wager(
        definition=defs.DONT_COME,
        player=player,
        game=game,
        value=25,
        target=5
    )
    
    assert player.bankroll == 1500
    assert wager not in game.wagers
    assert game.point is None
    assert wager.target == 5

    with pytest.raises(GameRuleViolation):
        game.place_wager(wager)

    assert player.bankroll == 1500
    assert wager not in game.wagers


def test_dont_come_placement_successful_on_point_roll(game_setup):
    game, player = game_setup
    game.roll(6)

    wager = Wager(
        definition=defs.DONT_COME,
        player=player,
        game=game,
        value=25
    )

    assert player.bankroll == 1500
    assert wager not in game.wagers
    assert game.point == 6
    assert wager.target is None

    game.place_wager(wager)

    assert player.bankroll == 1475
    assert wager in game.wagers


def test_dont_come_rejected_on_comeout_roll(game_setup):
    game, player = game_setup

    wager = Wager(
        definition=defs.DONT_COME,
        player=player,
        game=game,
        value=25
    )

    assert player.bankroll == 1500
    assert wager not in game.wagers
    assert game.point is None
    assert wager.target is None

    with pytest.raises(GameRuleViolation):
        game.place_wager(wager)
    
    assert player.bankroll == 1500
    assert wager not in game.wagers


def test_duplicate_rejection(dont_come_game):
    game, player, first_wager = dont_come_game

    wager_type = first_wager.definition.wager_type
    assert wager_type is WagerType.DONT_COME
    assert first_wager.player is player

    duplicate_wager = Wager(
        definition=defs.DONT_COME,
        player=player,
        game=game,
        value=100
    )

    with pytest.raises(
        GameRuleViolation
    ):
        game.place_wager(duplicate_wager)

    assert first_wager in game.wagers
    assert duplicate_wager not in game.wagers
    assert player.bankroll == 1475


def test_multiple_players_dont_trigger_duplicate_error(dont_come_game):
    
    game, player, wager = dont_come_game
    player2 = game.add_player()

    player2_wager = Wager(
        definition=defs.DONT_COME,
        player=player2,
        game=game,
        value=25
    )

    game.place_wager(player2_wager)

    assert wager in game.wagers
    assert player2_wager in game.wagers

    assert player.bankroll == 1475
    assert player2.bankroll == 1475


def test_travelled_dont_come_doesnt_trigger_duplicate_error(dont_come_game):
    game, player, first_wager = dont_come_game

    wager_type = first_wager.definition.wager_type
    assert wager_type is WagerType.DONT_COME
    assert first_wager.player is player

    second_wager = Wager(
        definition=defs.DONT_COME,
        player=player,
        game=game,
        value=25
        )

    game.roll(8)
    assert first_wager.target == 8

    game.place_wager(second_wager)
    
    assert first_wager in game.wagers
    assert second_wager in game.wagers
    assert player.bankroll == 1450



#=======================
# WAGER ADJUSTMENT TESTS
#=======================

def test_travelled_dont_come_take_down_successful_after_roll(dont_come_game):
    game, player, wager = dont_come_game

    game.roll(5)
    assert wager.target == 5

    game.take_down_wager(wager)

    assert wager not in game.wagers
    assert wager not in player.get_wagers()

    assert player.bankroll == 1500


def test_dont_come_take_down_successful_from_come_box(dont_come_game):
    game, player, wager = dont_come_game
    
    assert wager in game.wagers
    assert player.bankroll == 1475
    assert wager.target is None

    game.take_down_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_dont_come_cannot_be_turned_off(dont_come_game):
    game, player, wager = dont_come_game
    
    assert wager in game.wagers
    assert player.bankroll == 1475

    with pytest.raises(GameRuleViolation):
        game.set_wager_working_status(wager, False)

    assert wager.is_working is True
    assert wager in game.wagers
    assert player.bankroll == 1475
    
    game.roll(8)
    assert wager.target == 8

    with pytest.raises(GameRuleViolation):
        game.set_wager_working_status(wager, False)

    assert wager.is_working is True
    assert wager in game.wagers
    assert player.bankroll == 1475



#=======================
# RESOLUTION TESTS
#=======================


@pytest.mark.parametrize(
        "roll_sum, outcome, move_to",
        [
            (2, Resolution.WIN, None),
            (3, Resolution.WIN, None),
            (4, Resolution.MOVE, 4),
            (5, Resolution.MOVE, 5),
            (6, Resolution.MOVE, 6),
            (7, Resolution.LOSE, None),
            (8, Resolution.MOVE, 8),
            (9, Resolution.MOVE, 9),
            (10, Resolution.MOVE, 10),
            (11, Resolution.LOSE, None),
            (12, Resolution.PUSH, None),
        ]       
)
def test_untravelled_dont_come_bet_resolutions(
    dont_come_game,
    roll_sum,
    outcome,
    move_to
):
    game, _, wager = dont_come_game
    assert game.point is not None

    assert wager.target is None

    [result] = game.roll(roll_sum).wager_results
    
    assert result.resolution is outcome
    assert result.move_to == move_to


@pytest.mark.parametrize(
        "roll_sum",
        const.BOX_NUMS
)    
def test_dont_come_bet_travels_to_point(
    dont_come_game,
    roll_sum,
):
    game, _, wager = dont_come_game

    assert game.point is not None
    assert wager.target is None

    game.roll(roll_sum)

    assert wager.target == roll_sum
    assert wager in game.wagers


@pytest.mark.parametrize(
        "roll_sum, outcome",
        [
            (2, Resolution.NONE),
            (3, Resolution.NONE),
            (4, Resolution.NONE),
            (5, Resolution.NONE),
            (6, Resolution.NONE),
            (7, Resolution.WIN),
            (8, Resolution.LOSE),
            (9, Resolution.NONE),
            (10, Resolution.NONE),
            (11, Resolution.NONE),
            (12, Resolution.NONE),
        ]
        
)
def test_all_travelled_dont_come_resolutions_for_single_point(
    dont_come_game,
    roll_sum,
    outcome,
):
    game, _, wager = dont_come_game

    game.roll(8)
    assert wager.target == 8

    [result] = game.roll(roll_sum).wager_results
    
    assert result.resolution is outcome


@pytest.mark.parametrize(
        "point",
        const.BOX_NUMS
)
def test_travelled_dont_come_bet_loses_on_all_points(
    dont_come_game,
    point,
):
    game, _, wager = dont_come_game

    game.roll(point)
    assert wager.target == point

    [result] = game.roll(point).wager_results
    
    assert result.resolution is Resolution.LOSE


@pytest.mark.parametrize(
        "point",
        const.BOX_NUMS
)
def test_travelled_dont_come_all_points_win_on_7(
    dont_come_game,
    point,
):
    game, _, wager = dont_come_game

    game.roll(point)
    assert wager.target == point
    
    [result] = game.roll(7).wager_results
    
    assert result.resolution is Resolution.WIN


def test_travelled_dont_come_survives_point_reset(dont_come_game):
    game, player, wager = dont_come_game

    assert game.point == 6
    assert wager.target is None

    game.roll(5)
    assert wager.target == 5

    game.roll(6)
    assert game.point is None
    assert wager.target == 5

    assert wager in game.wagers
    assert wager.target == 5
    assert player.bankroll == 1475

    [result] = game.roll(7).wager_results

    assert result.resolution is Resolution.WIN
    assert result.profit == 25

    assert wager not in game.wagers
    assert game.point is None
    assert player.bankroll == 1525


def test_dont_come_box_loses_while_travelled_dont_come_wins(dont_come_game):
    game, player, wager1 = dont_come_game

    game.roll(8)

    wager2 = Wager(
        definition=defs.DONT_COME,
        player=player,
        game=game,
        value=25,
    )

    game.place_wager(wager2)

    assert player.bankroll == 1450

    results = game.roll(7).wager_results

    result1 = get_result(results, wager1)
    result2 = get_result(results, wager2)

    assert result1.resolution is Resolution.WIN
    assert result2.resolution is Resolution.LOSE

    assert result1.profit == 25
    assert result2.profit == 0

    assert wager1 not in game.wagers
    assert wager2 not in game.wagers
    assert player.bankroll == 1500
    assert game.point is None


def test_travelled_dont_come_loses_on_comeout_point(
    dont_come_game
):
    game, player, wager = dont_come_game

    game.roll(5)
    assert wager.target == 5

    game.roll(6)
    assert game.point is None

    [result] = game.roll(5).wager_results

    assert result.resolution is Resolution.LOSE
    assert wager not in game.wagers
    assert player.bankroll == 1475
    assert game.point == 5



#=======================
# PAYOUT TESTS
#=======================

@pytest.mark.parametrize(
    "roll",
    [2, 3, *const.BOX_NUMS]
)
def test_dont_come_pays_even_money(
    dont_come_game,
    roll,
):
    game, player, wager = dont_come_game
    assert wager.target is None

    if roll in (2,3):
        [result] = game.roll(roll).wager_results
    
    else:
        game.roll(roll)
        assert wager.target == roll
        [result] = game.roll(7).wager_results

    assert result.profit == 25
    assert result.resolution is Resolution.WIN



#=========================
# WAGER PERSISTENCE TESTS
#=========================

@pytest.mark.parametrize(
    "roll",
    [2, 3, *const.BOX_NUMS],
)
def test_dont_come_removed_after_win(
    dont_come_game,
    roll,
):
    game, player, wager = dont_come_game
    assert wager.target is None

    if roll in (2, 3):
        [result] = game.roll(roll).wager_results
    else:
        game.roll(roll)
        assert wager.target == roll
        [result] = game.roll(7).wager_results
    
    assert result.resolution is Resolution.WIN
    assert wager not in game.wagers
    assert player.bankroll == 1525


@pytest.mark.parametrize(
    "roll",
    [7, 11, *const.BOX_NUMS]
)
def test_dont_come_removed_after_loss(
    dont_come_game,
    roll,
):
    game, player, wager = dont_come_game

    if roll not in (7,11):
        game.roll(roll)
        assert wager.target == roll
        
    [result] = game.roll(roll).wager_results

    assert result.resolution is Resolution.LOSE
    assert wager not in game.wagers
    assert wager not in player.get_wagers()
    assert player.bankroll == 1475


def test_new_dont_come_replaces_losing_dont_come_on_same_point(dont_come_game):
    game, player, first_wager = dont_come_game

    second_wager = Wager(
        definition=defs.DONT_COME,
        player=player,
        game=game,
        value=25
        )

    game.roll(8)
    assert first_wager.target == 8

    game.place_wager(second_wager)

    assert first_wager in game.wagers
    assert second_wager in game.wagers

    results = game.roll(8).wager_results

    assert len(results) == 2

    old_result = get_result(results, first_wager)
    new_result = get_result(results, second_wager)

    assert old_result.resolution is Resolution.LOSE
    assert new_result.resolution is Resolution.MOVE
    assert new_result.move_to == 8

    assert first_wager not in game.wagers
    assert second_wager in game.wagers
    assert second_wager.target == 8

    assert old_result.profit == 0
    assert new_result.profit == 0
    assert second_wager.contract_max == 25

    assert player.bankroll == 1450


def test_dont_come_bet_stays_up_on_push(dont_come_game):
    game, player, wager = dont_come_game

    [result] = game.roll(12).wager_results
    
    assert result.resolution is Resolution.PUSH
    assert wager in game.wagers
    assert wager in player.get_wagers()

    assert wager.target is None
    assert result.profit == 0
    assert player.bankroll == 1475


#=========================
# CONTRACT TESTS
#=========================

def test_dont_come_contract_sets_with_point(dont_come_game):
    game, player, wager = dont_come_game
    
    assert wager.target is None
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
    assert player.bankroll == 1475

    game.decrease_wager(wager, 1)
    
    assert wager.value == 24
    assert player.bankroll == 1476


def test_dont_come_contract_decreases_with_value_after_roll(dont_come_game):
    game, player, wager = dont_come_game

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

    with pytest.raises(GameRuleViolation):
        game.increase_wager(wager, 11)
    assert wager.value ==  15
    assert player.bankroll == 1485
    
    game.roll(5)
    
    assert wager.value ==  15
    assert wager.contract_min is None
    assert wager.contract_max == 15

    with pytest.raises(GameRuleViolation):
        game.increase_wager(wager, 1)

    assert player.bankroll == 1485
    assert wager.value == 15


def test_dont_come_can_restore_value_before_next_roll(
    dont_come_game
):
    game, player, wager = dont_come_game

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

def test_dont_come_lifecycle(game_setup):
    game, player = game_setup

    wager1 = Wager(
        definition=defs.DONT_COME,
        player=player,
        game=game,
        value=25
    )
    
    wager2 = replace(wager1)
    wager3 = replace(wager1) 

    assert wager1 != wager2
    assert wager2 != wager3
    assert wager3 != wager1

    # Establish game point to allow DC bet
    game.roll(6)
    assert game.point == 6

    # Place first wager
    game.place_wager(wager1)
    assert wager1.target is None
    assert wager1 in game.wagers
    assert wager1 in player.get_wagers()
    assert player.bankroll == 1475

    # Increase wager value before locked in
    game.increase_wager(wager1, 10)
    assert wager1.value == 35
    assert player.bankroll == 1465

    # Move wager1 to target
    [result] = game.roll(9).wager_results
    assert result.resolution is Resolution.MOVE
    assert result.move_to == 9

    assert wager1.target == 9
    assert player.bankroll == 1465
    assert wager1 in game.wagers
    assert wager1 in player.get_wagers()
    assert wager2 not in game.wagers
    assert wager3 not in game.wagers

     # Place second DC bet
    game.place_wager(wager2)
    assert wager2 in game.wagers
    assert wager2 in player.get_wagers()
    assert wager2.target is None
    assert player.bankroll == 1440

    # Roll to move wager2 to point 5
    results = game.roll(5).wager_results

    result1 = get_result(results, wager1)
    result2 = get_result(results, wager2)

    assert result1.resolution is Resolution.NONE
    assert result2.resolution is Resolution.MOVE
    assert wager2.target == 5
    assert game.point == 6

    # Test wager2 contract
    with pytest.raises(GameRuleViolation):
        game.increase_wager(wager2, 10)
    assert wager2.value == 25
    assert player.bankroll == 1440

    game.decrease_wager(wager2, 20)
    assert wager2.value == 5
    
    game.increase_wager(wager2, 20)
    assert wager2.value == 25

    # Add a 3rd come bet
    game.place_wager(wager3)
    assert wager3.target is None
    assert wager3 in game.wagers
    assert wager3 in player.get_wagers()

    # DC wager3 loses in DC box on 11
    results = game.roll(11).wager_results

    result3 = get_result(results, wager3)
    
    assert result3.resolution is Resolution.LOSE
    assert result3.profit == 0
    assert player.bankroll == 1415
    assert wager3 not in game.wagers
    assert wager3 not in player.get_wagers()

    # Non-resolution roll
    results = game.roll(12).wager_results
    for result in results:
        assert result.resolution is Resolution.NONE
        assert result.profit == 0

    assert player.bankroll == 1415
    assert game.point == 6
    assert wager1.target == 9
    assert wager2.target == 5
    assert wager1 in game.wagers
    assert wager2 in game.wagers

    # Contract prevents upward adjustment
    for wager in (wager1, wager2):
        value = wager.value
        with pytest.raises(GameRuleViolation):
            game.increase_wager(wager, 10)
        assert wager.value == value

        # Contract allows downward adjustment
        game.decrease_wager(wager, 10)
        assert wager.value == value - 10

    assert player.bankroll == 1435

    # DC wager2 loses on 5
    results = game.roll(5).wager_results
    result = get_result(results, wager2)
    assert result.resolution is Resolution.LOSE
    assert result.profit == 0
    assert player.bankroll == 1435

    assert wager2 not in game.wagers
    assert wager1 in game.wagers
    assert wager1.target == 9

     # DC wager1 wins on 7 
    [result1] = game.roll(7).wager_results
    
    assert result1.resolution is Resolution.WIN
    assert result1.profit == 25
    assert player.bankroll == 1485
    assert wager1 not in game.wagers
    assert wager1 not in player.get_wagers()





    