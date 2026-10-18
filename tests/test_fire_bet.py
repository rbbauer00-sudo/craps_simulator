"""Integration tests for Fire Bet.

Uses the same game_setup fixture and game.roll(total) interface as
 test_ats_bets.py. Fire records DISTINCT points MADE by a shooter, not
points merely established or numbers rolled on comeout.
"""

import pytest
from conftest import result_for

from engine import constants as const
from engine import wager_definitions as defs
from engine.enums import Resolution, WagerType
from engine.exceptions import GameRuleViolation
from engine.wager import Wager, WagerResult
from engine.game import Game
from engine.player import Player

# Make every box point once. Each pair establishes and then makes a point.
BOX_POINTS = sorted(const.BOX_NUMS)


def place_fire(
        game: Game, 
        player: Player, 
        value: int = 5,
) -> Wager:
    wager = Wager(
        definition=defs.FIRE_BET,
        game=game,
        player=player,
        value=value,
    )
    game.place_wager(wager)
    return wager


def make_point(
        game: Game, 
        point: int, 
        wager: Wager
    ) -> WagerResult:
    """Establish and then make a point, checking both rolls."""
    assert game.point is None
    established = result_for(game.roll(point).wager_results, wager)
    assert established.resolution is Resolution.NONE
    assert game.point == point
    made = result_for(game.roll(point).wager_results, wager)
    assert game.point is None
    return made


@pytest.fixture
def fire_game(game_setup) -> tuple[Game, Player, Wager]:
    game, player = game_setup
    wager = place_fire(game, player)
    return game, player, wager


# =======================
# DEFINITION TESTS
# =======================

def test_fire_definition(game_setup):
    game, player = game_setup
    definition = defs.FIRE_BET
    wager = Wager(definition=definition, game=game, player=player, value=5)

    assert definition.wager_type is WagerType.FIRE_BET
    assert definition.name == "Fire Bet"
    assert definition.remove_after_win is True
    assert wager.definition is definition


# =======================
# PLACEMENT TESTS
# =======================

def test_fire_placement_initializes_tracking_and_charges_bankroll(game_setup):
    game, player = game_setup
    wager = place_fire(game, player)

    assert wager in game.wagers
    assert wager.targets_hit == set()
    assert player.bankroll == 1495
    assert wager.contract_min is None
    assert wager.contract_max is None


def test_fire_duplicate_rejected_without_charging_again(game_setup):
    game, player = game_setup
    wager = place_fire(game, player)
    bankroll_before = player.bankroll

    with pytest.raises(GameRuleViolation):
        place_fire(game, player)

    assert game.wagers == (wager,)
    assert player.bankroll == bankroll_before


@pytest.mark.parametrize("first_roll", [2, 4, 7, 11])
def test_fire_cannot_be_placed_after_shooters_first_roll(game_setup, first_roll):
    game, player = game_setup
    game.roll(first_roll)
    bankroll_before = player.bankroll

    with pytest.raises(GameRuleViolation):
        place_fire(game, player)

    assert player.bankroll == bankroll_before
    assert game.wagers == ()


def test_fire_can_be_placed_for_next_shooter_after_seven_out(game_setup):
    game, player = game_setup
    game.roll(4)  # Point established
    game.roll(7)  # Seven-out, new shooter's turn

    assert game.point is None
    assert game.shooter_roll_count == 0
    wager = place_fire(game, player)
    assert wager in game.wagers
    assert wager.targets_hit == set()


# =======================
# RESOLUTION TESTS
# =======================

@pytest.mark.parametrize("total", [2, 3, 7, 11, 12])
def test_comeout_roll_does_not_resolve_fire(fire_game, total):
    game, player, wager = fire_game
    result = result_for(game.roll(total).wager_results, wager)

    assert result.resolution is Resolution.NONE
    assert wager.targets_hit == set()
    assert wager in game.wagers
    assert game.point is None


def test_establishing_point_does_not_count_as_making_it(fire_game):
    game, player, wager = fire_game
    result = result_for(game.roll(6).wager_results, wager)

    assert result.resolution is Resolution.NONE
    assert wager.targets_hit == set()
    assert game.point == 6
    assert wager in game.wagers


@pytest.mark.parametrize("point", BOX_POINTS)
def test_each_box_point_is_recorded_only_when_made(game_setup, point):
    game, player = game_setup
    wager = place_fire(game, player)

    result = make_point(game, point, wager)
    assert result.resolution is Resolution.NONE
    assert wager.targets_hit == {point}
    assert wager in game.wagers


def test_repeatedly_making_same_point_counts_once(fire_game):
    game, player, wager = fire_game
    for _ in range(3):
        result = make_point(game, 6, wager)
        assert result.resolution is Resolution.NONE

    assert wager.targets_hit == {6}


def test_other_numbers_during_point_do_not_count(fire_game):
    game, player, wager = fire_game
    game.roll(6)
    for total in [2, 3, 4, 8, 11, 12]:
        result = result_for(game.roll(total).wager_results, wager)
        assert result.resolution is Resolution.NONE

    assert game.point == 6
    assert wager.targets_hit == set()


def test_comeout_seven_after_points_made_does_not_end_fire(fire_game):
    game, player, wager = fire_game
    make_point(game, 4, wager)
    result = result_for(game.roll(7).wager_results, wager)

    assert result.resolution is Resolution.NONE
    assert wager.targets_hit == {4}
    assert wager in game.wagers


@pytest.mark.parametrize("distinct_points", [0, 1, 2, 3])
def test_seven_out_before_four_distinct_points_loses(game_setup, distinct_points):
    game, player = game_setup
    wager = place_fire(game, player)

    for point in BOX_POINTS[:distinct_points]:
        make_point(game, point, wager)

    game.roll(10)  # Establish a point for seven-out
    result = result_for(game.roll(7).wager_results, wager)

    assert result.resolution is Resolution.LOSE
    assert len(wager.targets_hit) == distinct_points
    assert wager not in game.wagers


@pytest.mark.parametrize("distinct_points,multiple", [(4, 24), (5, 249)])
def test_seven_out_with_four_or_five_distinct_points_wins(
    game_setup, distinct_points, multiple
):
    game, player = game_setup
    starting_bankroll = player.bankroll
    wager = place_fire(game, player)

    for point in BOX_POINTS[:distinct_points]:
        result = make_point(game, point, wager)
        assert result.resolution is Resolution.NONE

    # On a new point, seven-out ends the shooter's hand.
    game.roll(BOX_POINTS[-1])
    result = result_for(game.roll(7).wager_results, wager)

    assert result.resolution is Resolution.WIN
    assert result.profit == wager.value * multiple
    assert wager not in game.wagers
    assert player.bankroll == starting_bankroll + wager.value * multiple


def test_sixth_distinct_point_wins_immediately(fire_game):
    game, player, wager = fire_game
    starting_bankroll = player.bankroll + wager.value

    for point in BOX_POINTS[:-1]:
        result = make_point(game, point, wager)
        assert result.resolution is Resolution.NONE
        assert wager in game.wagers

    result = make_point(game, BOX_POINTS[-1], wager)
    assert result.resolution is Resolution.WIN
    assert wager.targets_hit == set(BOX_POINTS)
    assert result.profit == wager.value * 999
    assert wager not in game.wagers
    assert player.bankroll == starting_bankroll + wager.value * 999


# =======================
# PAYOUT TESTS
# =======================

@pytest.mark.parametrize("count,multiple", [(4, 24), (5, 249), (6, 999)])
def test_fire_payout_rule_for_completed_targets(fire_game, count, multiple):
    game, player, wager = fire_game
    wager.targets_hit = set(BOX_POINTS[:count])
    assert defs.FIRE_BET.payout_rule(wager) == wager.value * multiple


@pytest.mark.parametrize("count", [0, 1, 2, 3])
def test_fire_payout_rule_rejects_nonwinning_target_count(fire_game, count):
    game, player, wager = fire_game
    wager.targets_hit = set(BOX_POINTS[:count])
    with pytest.raises(ValueError):
        defs.FIRE_BET.payout_rule(wager)


# =======================
# PERSISTENCE TESTS
# =======================

def test_fire_persists_across_point_cycles_and_comeout_sevens(fire_game):
    game, player, wager = fire_game

    make_point(game, 4, wager)
    game.roll(7)  # Comeout natural; does not end shooter
    make_point(game, 6, wager)
    game.roll(11)  # Comeout natural

    assert wager.targets_hit == {4, 6}
    assert wager in game.wagers


# =======================
# CONTRACT TESTS
# =======================

def test_fire_contract_locks_on_first_roll(fire_game):
    game, player, wager = fire_game
    assert wager.contract_min is None
    assert wager.contract_max is None

    game.roll(4)
    assert wager.contract_min == 5
    assert wager.contract_max == 5

    with pytest.raises(GameRuleViolation):
        game.decrease_wager(wager, 1)
    with pytest.raises(GameRuleViolation):
        game.take_down_wager(wager)

    assert wager.value == 5
    assert wager in game.wagers


def test_fire_contract_remains_locked_across_point_cycles(fire_game):
    game, player, wager = fire_game
    make_point(game, 4, wager)
    make_point(game, 5, wager)

    assert wager.contract_min == 5
    assert wager.contract_max == 5
    with pytest.raises(GameRuleViolation):
        game.increase_wager(wager, 1)
    assert wager.value == 5


# =======================
# LIFECYCLE TESTS
# =======================

def test_full_fire_loss_and_next_shooter_can_rebet(game_setup):
    game, player = game_setup
    initial_bankroll = player.bankroll
    original = place_fire(game, player)

    make_point(game, 4, original)
    game.roll(6)  # New point established
    result = result_for(game.roll(7).wager_results, original)

    assert result.resolution is Resolution.LOSE
    assert original not in game.wagers
    assert player.bankroll == initial_bankroll - 5
    assert game.shooter_roll_count == 0

    replacement = place_fire(game, player)
    assert replacement is not original
    assert replacement.targets_hit == set()
    assert replacement.contract_min is None
    assert replacement.contract_max is None


def test_full_fire_six_point_winning_shooter_lifecycle(game_setup):
    game, player = game_setup
    initial_bankroll = player.bankroll
    wager = place_fire(game, player)

    for point in BOX_POINTS:
        result = make_point(game, point, wager)

    assert result.resolution is Resolution.WIN
    assert wager.targets_hit == set(BOX_POINTS)
    assert game.point is None
    assert wager not in game.wagers
    assert player.bankroll == initial_bankroll + 5 * 999
