import pytest
from conftest import result_for

from craps_engine import wager_definitions as defs
from craps_engine.dice import RollResult
from craps_engine.enums import Resolution, WagerType
from craps_engine.exceptions import GameRuleViolation, InsufficientFundsError
from craps_engine.wager import Wager
from craps_engine.game import Game
from craps_engine.player import Player


STAKE = 25
ALL_TOTALS = range(2, 13)

# (definition, enum, display name, winning totals, profit multiplier)
# These ratios reflect earlier wager_definitions.py, not a universal casino pay table.
PROP_CASES = [
    (defs.ANY_CRAPS, WagerType.ANY_CRAPS, "Any Craps", {2, 3, 12}, 7),
    (defs.ANY_SEVEN, WagerType.ANY_SEVEN, "Any Seven", {7}, 4),
    (defs.YO_LEVEN, WagerType.YO_LEVEN, "Yo-Leven", {11}, 15),
    (defs.DEUCE, WagerType.DEUCE, "Deuce", {2}, 30),
    (defs.ACE_DEUCE, WagerType.ACE_DEUCE, "Ace-Deuce", {3}, 15),
    (defs.MIDNIGHT, WagerType.MIDNIGHT, "Midnight", {12}, 30),
]
PROP_IDS = ["any-craps", "any-seven", "yo-eleven", "deuce", "ace-deuce", "midnight"]


@pytest.fixture(params=PROP_CASES, ids=PROP_IDS)
def prop_case(request):
    return request.param


@pytest.fixture
def prop_game(
    game_setup, 
    prop_case,
) -> tuple[Game, Player, Wager]:
    game, player = game_setup
    definition, *_ = prop_case
    wager = Wager(
        definition=definition, 
        player=player,
        game=game, 
        value=STAKE,
    )

    game.place_wager(wager)
    return game, player, wager



# ==========================================================
# DEFINITION
# ==========================================================

def test_definition(prop_case):
    definition, wager_type, name, _, _ = prop_case
    assert definition.wager_type is wager_type
    assert definition.name == name
    assert definition.can_turn_off is False


def test_prop_cannot_be_turned_off(prop_game):
    _, _, wager = prop_game
    with pytest.raises(GameRuleViolation):
        wager.is_working = False
    assert wager.is_working is True


# ==========================================================
# PLACEMENT
# ==========================================================

@pytest.mark.parametrize("point", [None, 4, 5, 6, 8, 9, 10])
def test_placeable_regardless_of_table_point(game_setup, prop_case, point):
    game, player = game_setup
    definition, *_ = prop_case
    game._point = point
    wager = Wager(
        definition=definition, 
        player=player,
        game=game, 
        value=STAKE,
    )

    game.place_wager(wager)
    assert wager in game.wagers
    assert wager in player.get_wagers()
    assert player.bankroll == 1500 - STAKE


def test_duplicate_rejected_without_charging(prop_game):
    game, player, first = prop_game
    before = player.bankroll
    duplicate = Wager(
        definition=first.definition, 
        player=player,
        game=game, 
        value=10,
    )

    with pytest.raises(GameRuleViolation):
        game.place_wager(duplicate)
    assert duplicate not in game.wagers
    assert first in game.wagers
    assert player.bankroll == before


def test_different_prop_types_can_coexist(game_setup):
    game, player = game_setup
    wagers = [
        Wager(
            definition=case[0], 
            player=player, 
            game=game,
            value=10
        )
        for case in PROP_CASES
    ]

    for wager in wagers:
        game.place_wager(wager)
    assert all(wager in game.wagers for wager in wagers)
    assert len(game.wagers) == len(PROP_CASES)
    assert player.bankroll == 1500 - 10 * len(PROP_CASES)


def test_different_players_can_place_same_prop(prop_game):
    game, _, first = prop_game
    player2 = game.add_player()
    second = Wager(
        definition=first.definition,
        player=player2,
        game=game, 
        value=STAKE,
    )

    game.place_wager(second)
    assert first in game.wagers
    assert second in game.wagers
    assert player2.bankroll == 1500 - STAKE


@pytest.mark.parametrize("value", [0, -1, -25])
def test_nonpositive_prop_rejected(game_setup, prop_case, value):
    game, player = game_setup
    wager = Wager(
        definition=prop_case[0],
        player=player,
        game=game, 
        value=value,
    )

    with pytest.raises((GameRuleViolation, ValueError)):
        game.place_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_unaffordable_prop_rejected(game_setup, prop_case):
    game, player = game_setup
    wager = Wager(
        definition=prop_case[0], 
        player=player,
        game=game,
        value=player.bankroll + 1,
    )

    with pytest.raises(InsufficientFundsError):
        game.place_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_prop_can_be_taken_down_before_roll(prop_game):
    game, player, wager = prop_game
    game.take_down_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


# ==========================================================
# RESOLUTION: EXHAUSTIVE TOTALS
# ==========================================================

@pytest.mark.parametrize("total", ALL_TOTALS)
def test_single_wager_resolution_every_total(prop_game, prop_case, total):
    game, _, wager = prop_game
    winning_totals = prop_case[3]
    result = game._get_single_wager_result(wager, RollResult(total))
    expected = Resolution.WIN if total in winning_totals else Resolution.LOSE
    assert result.resolution is expected
    assert result.move_to is None
    assert result.wager is wager


@pytest.mark.parametrize("total", ALL_TOTALS)
def test_payout_every_total(prop_game, prop_case, total):
    game, _, wager = prop_game
    winning_totals, multiplier = prop_case[3:]
    result = game._get_single_wager_result(wager, RollResult(total))
    expected_profit = STAKE * multiplier if total in winning_totals else 0
    assert result.profit == expected_profit


@pytest.mark.parametrize("value", [1, 7, 25, 51])
def test_winning_profit_scales_with_stake(game_setup, prop_case, value):
    game, player = game_setup
    definition, _, _, winning_totals, multiplier = prop_case
    wager = Wager(
        definition=definition, 
        player=player,
        game=game, 
        value=value,
    )

    game.place_wager(wager)
    for winning_total in winning_totals:
        result = game._get_single_wager_result(wager, RollResult(winning_total))
        assert result.resolution is Resolution.WIN
        assert result.profit == value * multiplier


# ==========================================================
# PERSISTENCE / BANKROLL / FULL ROLL
# ==========================================================

@pytest.mark.parametrize("total", ALL_TOTALS)
def test_game_roll_executes_one_roll_prop(prop_game, prop_case, total):
    game, player, wager = prop_game
    wins, multiplier = prop_case[3:]
    results = game.roll(total).wager_results
    result = result_for(results, wager)

    if total in wins:
        assert result.resolution is Resolution.WIN
        assert result.profit == STAKE * multiplier
        if wager.definition.remove_after_win:
            assert wager not in game.wagers
            assert player.bankroll == 1500 + STAKE * multiplier
        else:
            assert wager in game.wagers
            assert player.bankroll == 1500 - STAKE + STAKE * multiplier
    else:
        assert result.resolution is Resolution.LOSE
        assert result.profit == 0
        assert wager not in game.wagers
        assert player.bankroll == 1500 - STAKE


def test_loser_cannot_resolve_again(prop_game, prop_case):
    game, player, wager = prop_game
    losing_total = next(t for t in ALL_TOTALS if t not in prop_case[3])
    first_results = game.roll(losing_total).wager_results
    assert result_for(first_results, wager).resolution is Resolution.LOSE
    after_loss = player.bankroll
    second_results = game.roll(next(iter(prop_case[3]))).wager_results
    assert all(r.wager is not wager for r in second_results)
    assert player.bankroll == after_loss


def test_winner_is_paid_once_per_roll(prop_game, prop_case):
    game, player, wager = prop_game
    winning_total = min(prop_case[3])
    multiplier = prop_case[4]
    first_results = game.roll(winning_total).wager_results
    assert result_for(first_results, wager).profit == STAKE * multiplier
    after_first = player.bankroll

    if wager.definition.remove_after_win:
        second_results = game.roll(winning_total).wager_results
        assert all(r.wager is not wager for r in second_results)
        assert player.bankroll == after_first
    else:
        second_results = game.roll(winning_total).wager_results
        assert result_for(second_results, wager).resolution is Resolution.WIN
        assert player.bankroll == after_first + STAKE * multiplier


def test_multiple_different_props_resolve_same_roll(game_setup):
    game, player = game_setup
    any_craps = Wager(
        definition=defs.ANY_CRAPS, 
        player=player,
        game=game,
        value=10,
    )

    ace_deuce = Wager(
        definition=defs.ACE_DEUCE, 
        player=player,
        game=game,
        value=10,
    )

    any_seven = Wager(
        definition=defs.ANY_SEVEN, 
        player=player,
        game=game,
        value=10,
    )

    for wager in (any_craps, ace_deuce, any_seven):
        game.place_wager(wager)

    results = game.roll(3).wager_results
    assert result_for(results, any_craps).resolution is Resolution.WIN
    assert result_for(results, ace_deuce).resolution is Resolution.WIN
    assert result_for(results, any_seven).resolution is Resolution.LOSE
    assert player.bankroll == (
        1500 - 30 + 10 * 7 + 10 * 15
        + (10 if any_craps.definition.remove_after_win else 0)
        + (10 if ace_deuce.definition.remove_after_win else 0)
    )


# ==========================================================
# NO PLAYER-TARGET / PARENT DEPENDENCIES
# ==========================================================

def test_no_point_target_or_parent_dependency(prop_game):
    _, _, wager = prop_game
    assert wager.target is None
    assert wager.parent_wager is None
    assert wager.contract_min is None
    assert wager.contract_max is None
