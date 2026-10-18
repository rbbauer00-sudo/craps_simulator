"""Integration tests for All Tall Small (ATS) bonus wagers.

Assumes game_setup supplies (game, player) and game.roll(total) returns
WagerResult objects for the wagers evaluated on that roll.
"""

import pytest
from conftest import result_for

from craps_engine import constants as const
from craps_engine import wager_definitions as defs
from craps_engine.enums import Resolution, WagerType
from craps_engine.exceptions import GameRuleViolation
from craps_engine.wager import Wager


ATS_CASES = [
    (defs.ATS_SMALL, WagerType.ATS_SMALL, const.ATS_SMALL_NUMS, 35),
    (defs.ATS_TALL, WagerType.ATS_TALL, const.ATS_TALL_NUMS, 35),
    (defs.ATS_ALL, WagerType.ATS_ALL, const.ATS_ALL_NUMS, 176),
]


def place_ats(game, player, definition, value=5):
    """Placement assigns the target and initializes targets_hit."""
    wager = Wager(definition=definition, game=game, player=player, value=value)
    game.place_wager(wager)
    return wager





@pytest.fixture
def ats_game(game_setup):
    game, player = game_setup
    wager = place_ats(game, player, defs.ATS_SMALL)
    return game, player, wager


# =======================
# DEFINITION TESTS
# =======================

@pytest.mark.parametrize("definition,wager_type,target,multiple", ATS_CASES)
def test_ats_definition(game_setup, definition, wager_type, target, multiple):
    game, player = game_setup
    assert definition.wager_type is wager_type
    wager = Wager(definition=definition, game=game, player=player, value=5)
    assert definition.payout_rule(wager) == 5 * multiple
    assert definition.remove_after_win is True


# =======================
# PLACEMENT TESTS
# =======================

@pytest.mark.parametrize("definition,wager_type,target,multiple", ATS_CASES)
def test_ats_placement_assigns_target_and_empty_history(
    game_setup, definition, wager_type, target, multiple
):
    game, player = game_setup
    wager = place_ats(game, player, definition)

    assert wager in game.wagers
    assert wager.target == target
    assert wager.targets_hit == set()
    assert player.bankroll == 1495


@pytest.mark.parametrize("definition,wager_type,target,multiple", ATS_CASES)
def test_ats_duplicate_rejected_without_charging_again(
    game_setup, definition, wager_type, target, multiple
):
    game, player = game_setup
    place_ats(game, player, definition)
    bankroll_before = player.bankroll

    with pytest.raises(GameRuleViolation):
        place_ats(game, player, definition)

    assert len(game.wagers) == 1
    assert player.bankroll == bankroll_before


def test_three_distinct_ats_components_can_coexist(game_setup):
    game, player = game_setup
    wagers = [place_ats(game, player, definition) for definition, *_ in ATS_CASES]

    assert len(game.wagers) == 3
    assert all(wager in game.wagers for wager in wagers)
    assert player.bankroll == 1485


def test_ats_rejected_after_non_seven_roll(game_setup):
    game, player = game_setup
    game.roll(4)
    bankroll_before = player.bankroll

    with pytest.raises(GameRuleViolation):
        place_ats(game, player, defs.ATS_SMALL)

    assert player.bankroll == bankroll_before
    assert game.wagers == ()


@pytest.mark.parametrize("initial_rolls", [[7], [4, 7]])
def test_ats_can_be_placed_after_any_seven(game_setup, initial_rolls):
    game, player = game_setup
    for total in initial_rolls:
        game.roll(total)

    wager = place_ats(game, player, defs.ATS_SMALL)
    assert wager in game.wagers
    assert wager.targets_hit == set()


# =======================
# RESOLUTION TESTS
# =======================

@pytest.mark.parametrize("definition,wager_type,target,multiple", ATS_CASES)
def test_relevant_roll_is_recorded_and_wager_stays_active(
    game_setup, definition, wager_type, target, multiple
):
    game, player = game_setup
    wager = place_ats(game, player, definition)
    total = min(target)

    results = game.roll(total).wager_results
    result = result_for(results, wager)

    assert result.resolution is Resolution.NONE
    assert wager.targets_hit == {total}
    assert wager in game.wagers


def test_ats_ignores_numbers_outside_its_target(game_setup):
    game, player = game_setup
    wager = place_ats(game, player, defs.ATS_SMALL)

    results = game.roll(8).wager_results
    result = result_for(results, wager)

    assert result.resolution is Resolution.NONE
    assert wager.targets_hit == set()


def test_repeated_number_only_counted_once(ats_game):
    game, player, wager = ats_game
    for _ in range(3):
        
        results = game.roll(2).wager_results
        result = result_for(results, wager)
        assert result.resolution is Resolution.NONE

    assert wager.targets_hit == {2}


@pytest.mark.parametrize("definition,wager_type,target,multiple", ATS_CASES)
def test_seven_loses_incomplete_ats(
    game_setup, definition, wager_type, target, multiple
):
    game, player = game_setup
    wager = place_ats(game, player, definition)
    
    results = game.roll(7).wager_results
    result = result_for(results, wager)

    assert result.resolution is Resolution.LOSE
    assert wager not in game.wagers


@pytest.mark.parametrize("definition,wager_type,target,multiple", ATS_CASES)
def test_ats_wins_only_after_all_required_numbers(
    game_setup, definition, wager_type, target, multiple
):
    game, player = game_setup
    wager = place_ats(game, player, definition)
    numbers = sorted(target)

    for total in numbers[:-1]:
        results = game.roll(total).wager_results
        result = result_for(results, wager)
        assert result.resolution is Resolution.NONE
        assert wager in game.wagers

    results = game.roll(numbers[-1]).wager_results
    final_result = result_for(results, wager)
    assert final_result.resolution is Resolution.WIN
    assert wager.targets_hit == set(target)
    assert wager not in game.wagers


# =======================
# PAYOUT TESTS
# =======================

@pytest.mark.parametrize("definition,wager_type,target,multiple", ATS_CASES)
def test_ats_payout_and_bankroll(
    game_setup, definition, wager_type, target, multiple
):
    game, player = game_setup
    starting_bankroll = player.bankroll
    wager = place_ats(game, player, definition, value=5)

    for total in sorted(target)[:-1]:
        game.roll(total)

    results = game.roll(sorted(target)[-1]).wager_results
    result = result_for(results, wager)
    assert result.resolution is Resolution.WIN
    assert result.profit == 5 * multiple
    assert player.bankroll == starting_bankroll + 5 * multiple


# =======================
# PERSISTENCE TESTS
# =======================

def test_all_components_resolve_independently(game_setup):
    game, player = game_setup
    small = place_ats(game, player, defs.ATS_SMALL)
    tall = place_ats(game, player, defs.ATS_TALL)
    all_bet = place_ats(game, player, defs.ATS_ALL)

    for total in [2, 3, 4, 5]:
        game.roll(total)

    results = game.roll(6).wager_results
    assert result_for(results, small).resolution is Resolution.WIN
    assert result_for(results, tall).resolution is Resolution.NONE
    assert result_for(results, all_bet).resolution is Resolution.NONE
    assert small not in game.wagers
    assert tall in game.wagers
    assert all_bet in game.wagers

    for total in [8, 9, 10, 11]:
        game.roll(total)

    results = game.roll(12).wager_results
    assert result_for(results, tall).resolution is Resolution.WIN
    assert result_for(results, all_bet).resolution is Resolution.WIN
    assert tall not in game.wagers
    assert all_bet not in game.wagers


# =======================
# CONTRACT TESTS
# =======================

def test_ats_contract_locks_on_first_roll(ats_game):
    game, player, wager = ats_game
    assert wager.contract_min is None
    assert wager.contract_max is None

    game.roll(2)

    assert wager.contract_min == 5
    assert wager.contract_max == 5

    with pytest.raises(GameRuleViolation):
        game.decrease_wager(wager, 1)

    with pytest.raises(GameRuleViolation):
        game.take_down_wager(wager)

    assert wager.value == 5
    assert wager in game.wagers


def test_rebet_after_seven_starts_with_fresh_history_and_contract(ats_game):
    game, player, original = ats_game
    game.roll(2)
    assert original.targets_hit == {2}
    assert original.contract_min == 5

    results = game.roll(7).wager_results
    result = result_for(results, original)
    assert result.resolution is Resolution.LOSE
    assert original not in game.wagers

    replacement = place_ats(game, player, defs.ATS_SMALL)
    assert replacement is not original
    assert replacement.targets_hit == set()
    assert replacement.contract_min is None
    assert replacement.contract_max is None

    game.roll(3)
    assert replacement.targets_hit == {3}
    assert replacement.contract_min == 5


# =======================
# LIFECYCLE TEST
# =======================

def test_three_ats_components_full_lifecycle(game_setup):
    game, player = game_setup
    starting_bankroll = player.bankroll

    small = place_ats(game, player, defs.ATS_SMALL)
    tall = place_ats(game, player, defs.ATS_TALL)
    all_bet = place_ats(game, player, defs.ATS_ALL)

    for total in [2, 3, 4, 5, 6, 8, 9, 10, 11]:
        game.roll(total)

    assert small not in game.wagers
    assert tall in game.wagers
    assert all_bet in game.wagers

    results = game.roll(12).wager_results
    assert result_for(results, tall).resolution is Resolution.WIN
    assert result_for(results, all_bet).resolution is Resolution.WIN
    assert game.wagers == ()

    expected_profit = 5 * (35 + 35 + 176)
    assert player.bankroll == starting_bankroll + expected_profit
