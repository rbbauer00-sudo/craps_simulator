"""Lay bet integration tests: placement, resolution, payout, refundable vig, lifecycle.

Assumes game_setup supplies (game, player) with $1,500 bankroll and that
Game.roll(total) returns WagerResult entries including Resolution.NONE.
"""

import pytest
from dataclasses import replace

from engine import wager_definitions as defs
from engine.enums import Resolution, VigSetting, WagerType
from engine.exceptions import GameRuleViolation, InsufficientFundsError
from engine.game import Game
from engine.player import Player
from engine.wager import Wager


STARTING_BANKROLL = 1500
BET = 120
BOX_NUMBERS = (4, 5, 6, 8, 9, 10)

# For a $120 Lay, the expected *integer-dollar* win and the 5% upfront vig.
# Lay ratios: 4/10 -> 1:2, 5/9 -> 2:3, 6/8 -> 5:6.
LAY_CASES = [
    (4, 60, 3),
    (5, 80, 4),
    (6, 100, 5),
    (8, 100, 5),
    (9, 80, 4),
    (10, 60, 3),
]


def make_lay(
    game: Game,
    player: Player,
    target: int = 4,
    value: int = BET,
) -> Wager:
    return Wager(
        definition=defs.LAY_BET,
        player=player,
        game=game,
        value=value,
        target=target,
    )


def roll_result(game: Game, wager: Wager, total: int):
    return next(result for result in game.roll(total).wager_results if result.wager is wager)


@pytest.fixture
def lay_bet_game(game_setup) -> tuple[Game, Player, Wager]:
    game, player = game_setup
    wager = make_lay(game, player)
    game.place_wager(wager)
    return game, player, wager


# =======================
# DEFINITION / PLACEMENT
# =======================

def test_lay_definition():
    definition = defs.LAY_BET
    assert definition.wager_type is WagerType.LAY_BET
    assert definition.name == "Lay"
    assert definition.can_turn_off is False
    assert definition.remove_after_win is False

@pytest.mark.parametrize("target, gross_win, vig", LAY_CASES)
@pytest.mark.parametrize("point", [None, 6])
def test_lay_placement(game_setup, target, gross_win, vig, point):
    game, player = game_setup
    game._point = point
    wager = make_lay(game, player, target)

    game.place_wager(wager)

    assert wager in game.wagers
    assert wager.value == BET
    assert wager.collected_vig == vig
    assert player.bankroll == STARTING_BANKROLL - BET - vig
    assert wager.is_buy is False


@pytest.mark.parametrize("target", [None, 2, 3, 7, 11, 12, 13])
def test_lay_invalid_target_rejected(game_setup, target):
    game, player = game_setup
    wager = make_lay(game, player, target=target)

    with pytest.raises(ValueError):
        game.place_wager(wager)

    assert wager not in game.wagers
    assert player.bankroll == STARTING_BANKROLL
    assert wager.collected_vig == 0


def test_lay_duplicate_rejected(lay_bet_game):
    game, player, first = lay_bet_game
    duplicate = make_lay(game, player, target=4)

    with pytest.raises(GameRuleViolation):
        game.place_wager(duplicate)

    assert first in game.wagers
    assert duplicate not in game.wagers
    assert player.bankroll == STARTING_BANKROLL - BET - 3


def test_lay_different_targets_allowed(lay_bet_game):
    game, player, first = lay_bet_game
    second = make_lay(game, player, target=6)
    game.place_wager(second)

    assert first in game.wagers
    assert second in game.wagers
    assert len(game.wagers) == 2
    assert player.bankroll == STARTING_BANKROLL - 2 * BET - 3 - 5


def test_lay_always_upfront_regardless_of_buy_vig_setting(game_setup):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        buy_vig_setting=VigSetting.ON_WIN,
    )
        
    game._settings = new_settings
    wager = make_lay(game, player)
    game.place_wager(wager)

    assert wager.collected_vig == 3
    assert player.bankroll == STARTING_BANKROLL - BET - 3


def test_lay_cannot_be_turned_off(lay_bet_game):
    game, player, wager = lay_bet_game
    with pytest.raises(GameRuleViolation):
        wager.is_working = False
    assert wager.is_working is True


def test_lay_cannot_be_changed_to_buy(lay_bet_game):
    game, player, wager = lay_bet_game
    with pytest.raises(ValueError):
        wager.is_buy = True
    assert wager.is_buy is False


# =======================
# RESOLUTION / PAYOUT
# =======================

@pytest.mark.parametrize("target, gross_win, vig", LAY_CASES)
def test_lay_wins_on_seven_and_renews_vig(game_setup, target, gross_win, vig):
    game, player = game_setup
    wager = make_lay(game, player, target)
    game.place_wager(wager)

    result = roll_result(game, wager, 7)

    assert result.resolution is Resolution.WIN
    assert result.profit == gross_win - vig
    assert player.bankroll == STARTING_BANKROLL - BET - vig + gross_win - vig
    assert wager in game.wagers
    assert wager.collected_vig == vig


@pytest.mark.parametrize("target, gross_win, vig", LAY_CASES)
def test_lay_loses_on_target(game_setup, target, gross_win, vig):
    game, player = game_setup
    wager = make_lay(game, player, target)
    game.place_wager(wager)

    result = roll_result(game, wager, target)

    assert result.resolution is Resolution.LOSE
    assert wager not in game.wagers
    assert player.bankroll == STARTING_BANKROLL - BET - vig


@pytest.mark.parametrize("roll", [2, 3, 5, 6, 8, 9, 10, 11, 12])
def test_lay_no_decision(lay_bet_game, roll):
    game, player, wager = lay_bet_game  # Lay 4
    result = roll_result(game, wager, roll)

    assert result.resolution is Resolution.NONE
    assert wager in game.wagers
    assert wager.collected_vig == 3
    assert player.bankroll == STARTING_BANKROLL - BET - 3


@pytest.mark.parametrize(
    "target, value, expected_gross, expected_vig",
    [
        (4, 25, 12, 1),
        (5, 25, 16, 1),
        (6, 25, 20, 1),
        (4, 100, 50, 2),  # Python round(2.5) -> 2
        (5, 100, 66, 3),  # Round vig on integer-dollar winnings
        (6, 100, 83, 4),
    ],
)
def test_lay_integer_payout_and_vig(
    game_setup, target, value, expected_gross, expected_vig
):
    game, player = game_setup
    wager = make_lay(game, player, target=target, value=value)
    game.place_wager(wager)

    assert wager.collected_vig == expected_vig
    result = roll_result(game, wager, 7)
    assert result.resolution is Resolution.WIN
    assert result.profit == expected_gross - expected_vig


# =======================
# ADJUSTMENT / REFUND
# =======================

def test_lay_increase_collects_only_additional_vig(lay_bet_game):
    game, player, wager = lay_bet_game  # $120 Lay 4, $3 vig
    game.increase_wager(wager, 80)  # $200 Lay 4, $5 vig

    assert wager.value == 200
    assert wager.collected_vig == 5
    assert player.bankroll == STARTING_BANKROLL - 200 - 5


def test_lay_decrease_refunds_excess_vig(lay_bet_game):
    game, player, wager = lay_bet_game
    game.decrease_wager(wager, 80)  # $40 Lay 4, $1 vig

    assert wager.value == 40
    assert wager.collected_vig == 1
    assert player.bankroll == STARTING_BANKROLL - 40 - 1


def test_lay_decrease_to_zero_refunds_principal_and_vig(lay_bet_game):
    game, player, wager = lay_bet_game
    game.decrease_wager(wager, BET)

    assert wager not in game.wagers
    assert player.bankroll == STARTING_BANKROLL


def test_lay_take_down_refunds_principal_and_vig(lay_bet_game):
    game, player, wager = lay_bet_game
    game.take_down_wager(wager)

    assert wager not in game.wagers
    assert player.bankroll == STARTING_BANKROLL


def test_lay_increase_insufficient_funds_is_atomic(lay_bet_game):
    game, player, wager = lay_bet_game
    bankroll_before = player.bankroll
    with pytest.raises((ValueError, InsufficientFundsError)):
        game.increase_wager(wager, bankroll_before + 1)

    assert wager.value == BET
    assert wager.collected_vig == 3
    assert player.bankroll == bankroll_before
    assert wager in game.wagers


# =======================
# LIFECYCLE
# =======================

def test_lay_two_wins_then_take_down(lay_bet_game):
    game, player, wager = lay_bet_game
    assert player.bankroll == 1377
    assert wager.collected_vig == 3

    for expected_bankroll in (1434, 1491):
        result = roll_result(game, wager, 7)
        assert result.resolution is Resolution.WIN
        assert result.profit == 57  # $60 win minus $3 next-cycle vig
        assert player.bankroll == expected_bankroll
        assert wager in game.wagers
        assert wager.collected_vig == 3

    game.take_down_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1614  # Two $60 wins less two earned $3 commissions


def test_lay_win_then_adjust_then_lose(lay_bet_game):
    game, player, wager = lay_bet_game

    assert roll_result(game, wager, 7).resolution is Resolution.WIN
    assert player.bankroll == 1434
    assert wager.collected_vig == 3

    game.increase_wager(wager, 80)
    assert wager.value == 200
    assert wager.collected_vig == 5
    assert player.bankroll == 1352

    assert roll_result(game, wager, 4).resolution is Resolution.LOSE
    assert wager not in game.wagers
    assert player.bankroll == 1352


def test_lay_no_decision_then_win_then_take_down(lay_bet_game):
    game, player, wager = lay_bet_game
    assert roll_result(game, wager, 6).resolution is Resolution.NONE
    assert player.bankroll == 1377
    assert wager.collected_vig == 3

    result = roll_result(game, wager, 7)
    assert result.resolution is Resolution.WIN
    assert result.profit == 57
    assert player.bankroll == 1434

    game.take_down_wager(wager)
    assert player.bankroll == 1557  # One $60 win, less the earned $3 vig

