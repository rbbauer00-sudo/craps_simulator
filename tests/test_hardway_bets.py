"""Hardway wager tests: definition, placement, exact dice resolution, payout,
working status, persistence, accounting and complete roll lifecycles.

Assumptions: defs.HARDWAY, WagerType.HARDWAY, $1,500 fixture bankroll,
7:1 on 4/10 and 9:1 on 6/8; win persistence follows remove_after_win.
Explicit dice are always passed as separate arguments to game.roll(*dice).
"""

import pytest
from conftest import result_for

from engine import wager_definitions as defs
from engine.dice import RollResult
from engine.enums import Resolution, WagerType
from engine.exceptions import GameRuleViolation, InsufficientFundsError
from engine.wager import Wager


DEF = defs.HARDWAY
STAKE = 10
HARD_DICE = {4: (2, 2), 6: (3, 3), 8: (4, 4), 10: (5, 5)}
EASY_DICE = {4: (1, 3), 6: (2, 4), 8: (2, 6), 10: (4, 6)}
PROFIT = {4: 70, 6: 90, 8: 90, 10: 70}
TARGETS = (4, 6, 8, 10)


def make_hardway(game, player, target=6, value=STAKE):
    wager = Wager(
        definition=DEF, 
        player=player,
        game=game, 
        value=value,
        target=target,
    )

    game.place_wager(wager)
    return wager


# ===================== DEFINITION =====================

def test_definition():
    assert DEF.wager_type is WagerType.HARDWAY
    assert DEF.can_turn_off is True


# ===================== PLACEMENT =====================

@pytest.mark.parametrize('target', TARGETS)
@pytest.mark.parametrize('point', [None, 5])
def test_valid_placement(game_setup, target, point):
    game, player = game_setup
    game._point = point
    wager = make_hardway(game, player, target)
    assert wager in game.wagers
    assert wager.target == target
    assert player.bankroll == 1500 - STAKE


@pytest.mark.parametrize('target', [None, 2, 3, 5, 7, 9, 11, 12])
def test_invalid_target_rejected(game_setup, target):
    game, player = game_setup
    wager = Wager(
        definition=DEF, 
        player=player,
        game=game, 
        value=STAKE,
        target=target,
    )

    with pytest.raises((GameRuleViolation, ValueError)):
        game.place_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_duplicate_same_target_rejected(game_setup):
    game, player = game_setup
    original = make_hardway(game, player, 6)
    before = player.bankroll
    duplicate = Wager(
        definition=DEF, 
        player=player,
        game=game, 
        value=20, 
        target=6,
    )

    with pytest.raises(GameRuleViolation):
        game.place_wager(duplicate)
    assert original in game.wagers
    assert duplicate not in game.wagers
    assert player.bankroll == before


def test_different_targets_coexist(game_setup):
    game, player = game_setup
    wagers = [make_hardway(game, player, target) for target in TARGETS]
    assert all(w in game.wagers for w in wagers)
    assert player.bankroll == 1500 - 4 * STAKE


def test_different_players_same_target(game_setup):
    game, player = game_setup
    other = game.add_player()
    first = make_hardway(game, player, 6)
    second = make_hardway(game, other, 6)
    assert first in game.wagers and second in game.wagers
    assert player.bankroll == 1500 - STAKE
    assert other.bankroll == 1500 - STAKE


@pytest.mark.parametrize('value', [0, -1, -10])
def test_nonpositive_amount_rejected(game_setup, value):
    game, player = game_setup
    wager = Wager(
        definition=DEF, 
        player=player,
        game=game, 
        value=value, 
        target=6,
    )

    with pytest.raises((GameRuleViolation, ValueError)):
        game.place_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_insufficient_funds_rejected(game_setup):
    game, player = game_setup
    wager = Wager(
        definition=DEF, 
        player=player,
        game=game, 
        value=player.bankroll + 1, 
        target=6,
    )
    
    with pytest.raises(InsufficientFundsError):
        game.place_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


# ===================== RESOLUTION =====================

@pytest.mark.parametrize('target', TARGETS)
def test_hard_combination_wins(game_setup, target):
    game, player = game_setup
    wager = make_hardway(game, player, target)
    result = game._get_single_wager_result(wager, RollResult(*HARD_DICE[target]))
    assert result.resolution is Resolution.WIN
    assert result.profit == PROFIT[target]


@pytest.mark.parametrize('target', TARGETS)
def test_easy_same_total_loses(game_setup, target):
    game, player = game_setup
    wager = make_hardway(game, player, target)
    for dice in (EASY_DICE[target], EASY_DICE[target][::-1]):
        result = game._get_single_wager_result(wager, RollResult(*dice))
        assert result.resolution is Resolution.LOSE
        assert result.profit == 0


@pytest.mark.parametrize('target', TARGETS)
@pytest.mark.parametrize('dice', [(1, 6), (2, 5), (3, 4)])
def test_seven_loses(game_setup, target, dice):
    game, player = game_setup
    wager = make_hardway(game, player, target)
    result = game._get_single_wager_result(wager, RollResult(*dice))
    assert result.resolution is Resolution.LOSE
    assert result.profit == 0


@pytest.mark.parametrize('target', TARGETS)
def test_all_other_combinations_are_none(game_setup, target):
    game, player = game_setup
    wager = make_hardway(game, player, target)
    for d1 in range(1, 7):
        for d2 in range(1, 7):
            dice = (d1, d2)
            roll = RollResult(*dice)
            if roll.total in (7, target):
                continue
            result = game._get_single_wager_result(wager, roll)
            assert result.resolution is Resolution.NONE, (target, dice)
            assert result.profit == 0


# ===================== PAYOUT =====================

@pytest.mark.parametrize('target', TARGETS)
@pytest.mark.parametrize('stake', [1, 7, 10, 25])
def test_profit_scales_with_stake(game_setup, target, stake):
    game, player = game_setup
    wager = make_hardway(game, player, target, stake)
    result = game._get_single_wager_result(wager, RollResult(*HARD_DICE[target]))
    ratio = 7 if target in (4, 10) else 9
    assert result.profit == stake * ratio


# ===================== WORKING STATUS =====================

@pytest.mark.parametrize('target', TARGETS)
def test_nonworking_hardway_ignores_hard_hit_and_seven(game_setup, target):
    game, player = game_setup
    wager = make_hardway(game, player, target)
    wager.is_working = False
    assert wager.is_working is False
    for dice in (HARD_DICE[target], EASY_DICE[target], (3, 4)):
        result = game._get_single_wager_result(wager, RollResult(*dice))
        assert result.resolution is Resolution.NONE
        assert result.profit == 0


def test_working_status_can_toggle_back_on(game_setup):
    game, player = game_setup
    wager = make_hardway(game, player, 6)
    wager.is_working = False
    wager.is_working = True
    assert wager.is_working is True
    assert game._get_single_wager_result(wager, RollResult(3, 3)).resolution is Resolution.WIN


# ===================== PERSISTENCE / LIFECYCLE =====================

@pytest.mark.parametrize('target', TARGETS)
def test_unrelated_roll_keeps_wager_and_bankroll(game_setup, target):
    game, player = game_setup
    wager = make_hardway(game, player, target)
    before = player.bankroll
    results = game.roll(1, 2).wager_results
    assert result_for(results, wager).resolution is Resolution.NONE
    assert wager in game.wagers
    assert player.bankroll == before


@pytest.mark.parametrize('target', TARGETS)
def test_easy_hit_loses_stake(game_setup, target):
    game, player = game_setup
    wager = make_hardway(game, player, target)
    result = result_for(game.roll(*EASY_DICE[target]).wager_results, wager)
    assert result.resolution is Resolution.LOSE
    assert wager not in game.wagers
    assert player.bankroll == 1500 - STAKE


@pytest.mark.parametrize('target', TARGETS)
def test_hard_hit_pays_and_applies_win_persistence(game_setup, target):
    game, player = game_setup
    wager = make_hardway(game, player, target)
    result = result_for(game.roll(*HARD_DICE[target]).wager_results, wager)
    assert result.resolution is Resolution.WIN
    assert result.profit == PROFIT[target]
    assert (wager in game.wagers) is (not DEF.remove_after_win)
    expected = 1500 + PROFIT[target] - (STAKE if not DEF.remove_after_win else 0)
    assert player.bankroll == expected


def test_nonworking_wager_survives_actual_roll(game_setup):
    game, player = game_setup
    wager = make_hardway(game, player, 6)
    wager.is_working = False
    before = player.bankroll
    results = game.roll(3, 3).wager_results
    assert result_for(results, wager).resolution is Resolution.NONE
    assert wager in game.wagers
    assert player.bankroll == before


def test_takedown_refunds_exactly_once(game_setup):
    game, player = game_setup
    wager = make_hardway(game, player, 6)
    game.take_down_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500
    with pytest.raises(GameRuleViolation):
        game.take_down_wager(wager)
    assert player.bankroll == 1500


def test_multiple_hardways_same_roll_different_outcomes(game_setup):
    game, player = game_setup
    hard4 = make_hardway(game, player, 4)
    hard6 = make_hardway(game, player, 6)
    hard8 = make_hardway(game, player, 8)
    hard10 = make_hardway(game, player, 10)
    before = player.bankroll
    results = game.roll(3, 3).wager_results
    assert result_for(results, hard4).resolution is Resolution.NONE
    assert result_for(results, hard6).resolution is Resolution.WIN
    assert result_for(results, hard8).resolution is Resolution.NONE
    assert result_for(results, hard10).resolution is Resolution.NONE
    assert player.bankroll == before + 90 + (STAKE if DEF.remove_after_win else 0)


def test_multiple_hardways_all_lose_on_seven(game_setup):
    game, player = game_setup
    wagers = [make_hardway(game, player, target) for target in TARGETS]
    results = game.roll(3, 4).wager_results
    assert all(result_for(results, w).resolution is Resolution.LOSE for w in wagers)
    assert all(w not in game.wagers for w in wagers)
    assert player.bankroll == 1500 - 4 * STAKE
