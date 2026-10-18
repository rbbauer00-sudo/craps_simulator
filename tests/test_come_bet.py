import pytest
from dataclasses import replace
from conftest import get_result

from craps_engine import wager_definitions as defs
from craps_engine import constants as const
from craps_engine.game import Game
from craps_engine.player import Player
from craps_engine.wager import Wager
from craps_engine.enums import Resolution, WagerType
from craps_engine.exceptions import GameRuleViolation

@pytest.fixture
def come_bet_game(game_setup) -> tuple[Game, Player, Wager]:
    game, player = game_setup

    wager = Wager(
        definition=defs.COME,
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

def test_come_bet_definition():
    wager_def = defs.COME

    assert wager_def.wager_type is WagerType.COME
    assert wager_def.name == "Come"
    assert wager_def.can_turn_off is False
    assert wager_def.remove_after_win is True



#=======================
#PLACEMENT TESTS
#=======================

def test_come_bet_error_if_placed_with_target(game_setup):
    game, player = game_setup
    
    wager = Wager(
        definition=defs.COME,
        player=player,
        game=game,
        value=25,
        target=5
    )
    
    assert player.bankroll == 1500
    assert wager not in game.wagers
    assert game.point is None

    with pytest.raises(GameRuleViolation):
        game.place_wager(wager)

    assert player.bankroll == 1500
    assert wager not in game.wagers


def test_come_bet_placement_successful_on_point_roll(game_setup):
    game, player = game_setup
    game.roll(6)

    wager = Wager(
        definition=defs.COME,
        player=player,
        game=game,
        value=25
    )

    assert player.bankroll == 1500
    assert wager not in game.wagers
    assert game.point == 6

    game.place_wager(wager)

    assert player.bankroll == 1475
    assert wager in game.wagers


def test_come_bet_rejected_on_comeout_roll(game_setup):
    game, player = game_setup

    wager = Wager(
        definition=defs.COME,
        player=player,
        game=game,
        value=25
    )

    assert player.bankroll == 1500
    assert wager not in game.wagers
    assert game.point is None

    with pytest.raises(GameRuleViolation):
        game.place_wager(wager)
    
    assert player.bankroll == 1500
    assert wager not in game.wagers


def test_duplicate_rejection(come_bet_game):
    game, player, first_wager = come_bet_game

    wager_type = first_wager.definition.wager_type
    assert wager_type is WagerType.COME
    assert first_wager.player is player

    duplicate_wager = Wager(
        definition=defs.COME,
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


def test_multiple_players_dont_trigger_duplicate_error(come_bet_game):
    
    game, player, wager = come_bet_game
    player2 = game.add_player()

    player2_wager = Wager(
        definition=defs.COME,
        player=player2,
        game=game,
        value=25
    )

    game.place_wager(player2_wager)

    assert wager in game.wagers
    assert player2_wager in game.wagers

    assert player.bankroll == 1475
    assert player2.bankroll == 1475


def test_travelled_come_doesnt_trigger_duplicate_error(come_bet_game):
    game, player, first_wager = come_bet_game

    wager_type = first_wager.definition.wager_type
    assert wager_type is WagerType.COME
    assert first_wager.player is player

    second_wager = Wager(
        definition=defs.COME,
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

def test_travelled_come_bet_take_down_rejection_after_roll(come_bet_game):
    game, player, wager = come_bet_game

    game.roll(5)
    assert wager.target == 5

    with pytest.raises(GameRuleViolation):
        game.take_down_wager(wager)

    assert wager in game.wagers
    assert wager in player.get_wagers()

    assert player.bankroll == 1475


def test_come_bet_take_down_successful_from_come_box(come_bet_game):
    game, player, wager = come_bet_game
    
    assert wager in game.wagers
    assert player.bankroll == 1475
    assert wager.target is None

    game.take_down_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_come_bet_cannot_be_turned_off(come_bet_game):
    game, player, wager = come_bet_game
    
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
            (2, Resolution.LOSE, None),
            (3, Resolution.LOSE, None),
            (4, Resolution.MOVE, 4),
            (5, Resolution.MOVE, 5),
            (6, Resolution.MOVE, 6),
            (7, Resolution.WIN, None),
            (8, Resolution.MOVE, 8),
            (9, Resolution.MOVE, 9),
            (10, Resolution.MOVE, 10),
            (11, Resolution.WIN, None),
            (12, Resolution.LOSE, None),
        ]       
)
def test_untravelled_come_bet_resolutions(
    come_bet_game,
    roll_sum,
    outcome,
    move_to
):
    game, _, wager = come_bet_game
    assert game.point is not None

    assert wager.target is None

    [result] = game.roll(roll_sum).wager_results
    
    assert result.resolution is outcome
    assert result.move_to is move_to


@pytest.mark.parametrize(
        "roll_sum",
        const.BOX_NUMS
)    
def test_come_bet_travels_to_point(
    come_bet_game,
    roll_sum,
):
    game, _, wager = come_bet_game

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
            (7, Resolution.LOSE),
            (8, Resolution.WIN),
            (9, Resolution.NONE),
            (10, Resolution.NONE),
            (11, Resolution.NONE),
            (12, Resolution.NONE),
        ]
        
)
def test_all_travelled_come_resolutions_for_single_point(
    come_bet_game,
    roll_sum,
    outcome,
):
    game, _, wager = come_bet_game
    
    game.roll(8)
    assert wager.target == 8

    [result] = game.roll(roll_sum).wager_results
    
    assert result.resolution is outcome


@pytest.mark.parametrize(
        "point",
        const.BOX_NUMS
)
def test_travelled_come_bet_wins_on_all_points(
    come_bet_game,
    point,
):
    game, _, wager = come_bet_game

    game.roll(point)
    assert wager.target == point

    [result] = game.roll(point).wager_results
    
    assert result.resolution is Resolution.WIN


@pytest.mark.parametrize(
        "point",
        const.BOX_NUMS
)
def test_travelled_come_all_points_lose_on_7(
    come_bet_game,
    point,
):
    game, _, wager = come_bet_game
    
    game.roll(point)
    assert wager.target == point

    [result] = game.roll(7).wager_results
    
    assert result.resolution is Resolution.LOSE


def test_travelled_come_survives_point_reset(come_bet_game):
    game, player, wager = come_bet_game

    assert game.point == 6

    game.roll(5)
    assert wager.target == 5

    game.roll(6)
    assert game.point is None

    assert wager in game.wagers
    assert wager.target == 5
    assert player.bankroll == 1475

    [result] = game.roll(5).wager_results

    assert result.resolution is Resolution.WIN
    assert result.profit == 25

    assert wager not in game.wagers
    assert game.point == 5
    assert player.bankroll == 1525


def test_travelled_come_loses_on_comeout_seven(come_bet_game):
    game, player, wager = come_bet_game

    game.roll(5)
    game.roll(6)

    assert game.point is None
    assert wager.target == 5

    [result] = game.roll(7).wager_results

    assert result.resolution is Resolution.LOSE
    assert wager not in game.wagers
    assert player.bankroll == 1475
    assert game.point is None


def test_come_box_wins_while_travelled_come_loses(come_bet_game):
    game, player, wager1 = come_bet_game

    game.roll(8)

    wager2 = Wager(
        definition=defs.COME,
        player=player,
        game=game,
        value=25,
    )

    game.place_wager(wager2)

    assert player.bankroll == 1450

    results = game.roll(7).wager_results

    result1 = get_result(results, wager1)
    result2 = get_result(results, wager2)

    assert result1.resolution is Resolution.LOSE
    assert result2.resolution is Resolution.WIN

    assert result1.profit == 0
    assert result2.profit == 25

    assert wager1 not in game.wagers
    assert wager2 not in game.wagers
    assert player.bankroll == 1500
    assert game.point is None



#=======================
# PAYOUT TESTS
#=======================

@pytest.mark.parametrize(
    "roll",
    [7, 11, 4, 5, 6, 8, 9, 10]
)
def test_come_bet_pays_even_money(
    come_bet_game,
    roll,
):
    game, player, wager = come_bet_game
    assert wager.target is None

    if roll not in (7, 11):
        game.roll(roll)
        assert wager.target == roll
    
    [result] = game.roll(roll).wager_results

    assert result.resolution is Resolution.WIN
    assert result.profit == 25
    assert player.bankroll == 1525



#=========================
# WAGER PERSISTENCE TESTS
#=========================

@pytest.mark.parametrize(
    "roll",
    [7, 11, 4, 5, 6, 8, 9, 10],
)
def test_come_bet_removed_after_win(
    come_bet_game,
    roll,
):
    game, player, wager = come_bet_game
    assert wager.target is None

    if roll not in (7, 11):
        game.roll(roll)
        assert wager.target == roll
    
    [result] = game.roll(roll).wager_results
    
    
    assert result.resolution is Resolution.WIN
    assert wager not in game.wagers
    assert player.bankroll == 1525


@pytest.mark.parametrize(
    "roll",
    [2, 3, 12, 4, 5, 6, 8, 9, 10]
)
def test_come_bet_removed_after_loss(
    come_bet_game,
    roll,
):
    game, player, wager = come_bet_game

    game.roll(roll)

    if roll not in (2, 3, 12):
        assert wager.target == roll
        game.roll(7)

    assert wager not in game.wagers
    assert wager not in player.get_wagers()
    assert player.bankroll == 1475


def test_new_come_bet_replaces_winning_come_on_same_point(come_bet_game):
    game, player, first_wager = come_bet_game

    second_wager = Wager(
        definition=defs.COME,
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

    assert old_result.resolution is Resolution.WIN
    assert new_result.resolution is Resolution.MOVE
    assert new_result.move_to == 8

    assert first_wager not in game.wagers
    assert second_wager in game.wagers
    assert second_wager.target == 8

    assert player.bankroll == 1500



#=========================
# CONTRACT TESTS
#=========================

def test_come_bet_contract_sets_with_point(come_bet_game):
    game, player, wager = come_bet_game
    new_settings = replace(
        game.settings,
        allow_put_bets=False,
    )
        
    game._settings = new_settings
    
    assert wager.target is None
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




#=======================
# PUT COME TESTS
#=======================

@pytest.mark.parametrize("target", sorted(const.BOX_NUMS - {6}))
def test_put_come_direct_placement_on_other_number(game_setup, target):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        allow_put_bets=True,
    )
        
    game._settings = new_settings
    game.roll(6)
    wager = Wager(
        definition=defs.COME, 
        player=player,
        game=game, 
        value=25, 
        target=target,
    )

    game.place_wager(wager)
    assert wager in game.wagers
    assert wager.target == target
    assert wager.contract_min is None
    assert wager.contract_max is None
    assert player.bankroll == 1475


@pytest.mark.parametrize("target", sorted(const.BOX_NUMS - {6}))
def test_put_come_disabled_rejects_direct_placement(game_setup, target):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        allow_put_bets=False,
    )
        
    game._settings = new_settings
    game.roll(6)
    wager = Wager(
        definition=defs.COME, 
        player=player,
        game=game, 
        value=25, 
        target=target,
    )

    with pytest.raises(GameRuleViolation):
        game.place_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_put_come_cannot_target_current_table_point(game_setup):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        allow_put_bets=True,
    )
        
    game._settings = new_settings
    game.roll(6)
    wager = Wager(
        definition=defs.COME, 
        player=player,
        game=game, 
        value=25, 
        target=6,
    )

    with pytest.raises(GameRuleViolation):
        game.place_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_put_come_requires_table_point(game_setup):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        allow_put_bets=True,
    )
        
    game._settings = new_settings
    wager = Wager(
        definition=defs.COME, 
        player=player,
        game=game, 
        value=25, 
        target=5,
    )

    with pytest.raises(GameRuleViolation):
        game.place_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_put_come_rejects_duplicate_target(game_setup):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        allow_put_bets=True,
    )
        
    game._settings = new_settings
    game.roll(6)
    first = Wager(
        definition=defs.COME, 
        player=player,
        game=game, 
        value=25, 
        target=5,
    )
    
    duplicate = Wager(
        definition=defs.COME, 
        player=player,
        game=game, 
        value=25, 
        target=5,
    )

    game.place_wager(first)

    with pytest.raises(GameRuleViolation):
        game.place_wager(duplicate)
    assert first in game.wagers
    assert duplicate not in game.wagers
    assert player.bankroll == 1475


def test_put_come_allows_different_established_targets(game_setup):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        allow_put_bets=True,
    )
        
    game._settings = new_settings
    game.roll(6)
    first = Wager(
        definition=defs.COME, 
        player=player,
        game=game, 
        value=25, 
        target=5,
    )

    second = Wager(
        definition=defs.COME, 
        player=player,
        game=game, 
        value=25, 
        target=8,
    )

    game.place_wager(first)
    game.place_wager(second)
    assert first in game.wagers
    assert second in game.wagers
    assert player.bankroll == 1450


@pytest.mark.parametrize("winning", [True, False], ids=["win", "lose"])
def test_put_come_direct_placement_resolves(game_setup, winning):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        allow_put_bets=True,
    )
        
    game._settings = new_settings
    game.roll(6)
    wager = Wager(
        definition=defs.COME, 
        player=player,
        game=game, 
        value=25, 
        target=5,
    )

    game.place_wager(wager)

    [result] = game.roll(5 if winning else 7).wager_results
    assert result.resolution is (Resolution.WIN if winning else Resolution.LOSE)
    assert result.profit == (25 if winning else 0)
    assert wager not in game.wagers  # Come wagers resolve and come down.
    assert player.bankroll == (1525 if winning else 1475)

def test_put_come_direct_placement_contracts_on_first_roll(game_setup):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        allow_put_bets=True,
    )
        
    game._settings = new_settings
    game.roll(6)
    wager = Wager(
        definition=defs.COME, 
        player=player,
        game=game, 
        value=25, 
        target=5,
    )

    game.place_wager(wager)
    game.increase_wager(wager, 20)
    assert wager.contract_min is None
    assert player.bankroll == 1455

    game.roll(9)  # Neither the Come number nor seven.
    assert wager in game.wagers
    assert wager.contract_min == 45
    assert wager.contract_max is None
    with pytest.raises(GameRuleViolation):
        game.decrease_wager(wager, 1)
    assert wager.value == 45
    assert player.bankroll == 1455


def test_put_come_increase_and_contract_ratchet(come_bet_game):
    game, player, wager = come_bet_game
    new_settings = replace(
        game.settings,
        allow_put_bets=True,
    )
        
    game._settings = new_settings
    game.roll(5)  # Come wager travels to 5; table point stays 6.

    assert wager.contract_min == 25
    assert wager.contract_max is None
    game.increase_wager(wager, 50)
    assert wager.value == 75
    assert wager.contract_min == 25
    assert player.bankroll == 1425

    game.decrease_wager(wager, 30)
    assert wager.value == 45
    assert wager.contract_min == 25
    assert player.bankroll == 1455

    game.roll(9)
    assert wager.contract_min == 45
    assert wager.contract_max is None
    with pytest.raises(GameRuleViolation):
        game.decrease_wager(wager, 1)
    assert wager.value == 45

    game.increase_wager(wager, 5)
    [result] = game.roll(5).wager_results
    assert result.resolution is Resolution.WIN
    assert result.profit == 50
    assert wager not in game.wagers
    assert player.bankroll == 1550


def test_put_come_increase_loses_full_amount(come_bet_game):
    game, player, wager = come_bet_game
    new_settings = replace(
        game.settings,
        allow_put_bets=True,
    )
        
    game._settings = new_settings
    game.roll(5)
    game.increase_wager(wager, 50)

    [result] = game.roll(7).wager_results
    assert result.resolution is Resolution.LOSE
    assert wager not in game.wagers
    assert player.bankroll == 1425


def test_put_come_disabled_increase_preserves_funds(come_bet_game):
    game, player, wager = come_bet_game
    new_settings = replace(
        game.settings,
        allow_put_bets=False,
    )
        
    game._settings = new_settings
    game.roll(5)
    assert wager.contract_min == 25
    assert wager.contract_max == 25

    with pytest.raises(GameRuleViolation):
        game.increase_wager(wager, 50)
    assert wager.value == 25
    assert player.bankroll == 1475



#=========================
# LIFECYCLE TEST
#=========================

def test_come_bet_lifecycle(game_setup):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        allow_put_bets=False,
    )
        
    game._settings = new_settings

    wager1 = Wager(
        definition=defs.COME,
        player=player,
        game=game,
        value=25
    )

    wager2 = replace(wager1)
    wager3 = replace(wager1)

    assert wager1 is not wager2
    assert wager2 is not wager3
    assert wager3 is not wager1

    # Establish game point to allow come bet
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

    # Place second come bet
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

    with pytest.raises(GameRuleViolation):
        game.decrease_wager(wager2, 20)
    assert wager2.value == 25

    # Add a 3rd come bet
    game.place_wager(wager3)
    assert wager3.target is None
    assert wager3 in game.wagers
    assert wager3 in player.get_wagers()

    # 3rd come bet natural win
    results = game.roll(11).wager_results

    result3 = get_result(results, wager3)

    assert result3.resolution is Resolution.WIN
    assert result3.profit == 25
    assert player.bankroll == 1465
    assert wager3 not in game.wagers
    assert wager3 not in player.get_wagers()
    
    # Non-resolution roll
    results = game.roll(12).wager_results
    for result in results:
        assert result.resolution is Resolution.NONE
        assert result.profit == 0

    assert player.bankroll == 1465
    assert game.point == 6
    assert wager1 in game.wagers
    assert wager2 in game.wagers

    # Contract prevents adjustment
    for wager in (wager1, wager2):
        value = wager.value
        with pytest.raises(GameRuleViolation):
            game.increase_wager(wager, 10)
        assert wager.value == value

        with pytest.raises(GameRuleViolation):
            game.decrease_wager(wager, 10)
        assert wager.value == value

    assert player.bankroll == 1465

    # Come point winner 
    results = game.roll(9).wager_results
    result1 = get_result(results, wager1)

    assert result1.resolution is Resolution.WIN
    assert result1.profit == 35
    assert player.bankroll == 1535
    assert wager1 not in game.wagers
    assert wager1 not in player.get_wagers()

    # Come bet loser
    [result] = game.roll(7).wager_results
    assert result.resolution is Resolution.LOSE
    assert result.profit == 0
    assert player.bankroll == 1535

    # Game back to initial state
    assert wager2 not in game.wagers
    assert wager2 not in player.get_wagers()
    assert game.point is None
    assert game.wagers == ()
    assert player.get_wagers() == []
    assert player.bankroll == 1535
