"""Buy bet tests: shared Place definition, payouts, vig, conversion, lifecycle."""

import pytest
from dataclasses import replace

from craps_engine import wager_definitions as defs
from craps_engine.enums import Resolution, VigSetting, WagerType
from craps_engine.exceptions import GameRuleViolation
from craps_engine.game import Game
from craps_engine.player import Player
from craps_engine.wager import Wager


STARTING_BANKROLL = 1500
BET = 100


@pytest.fixture
def buy_game(game_setup) -> tuple[Game, Player]:
    game, player = game_setup

    new_settings = replace(
        game.settings,
        buy_vig_setting=VigSetting.ON_WIN,
    )
    
    game._settings = new_settings
    return game, player


@pytest.fixture
def buy_bet_game(buy_game) -> tuple[Game, Player, Wager]:
    game, player = buy_game
    wager = make_buy(game, player, target=4, value=BET)
    game.place_wager(wager)
    return game, player, wager


def make_buy(game: Game, player: Player, target: int = 4, value: int = BET) -> Wager:
    return Wager(
        definition=defs.PLACE_BET,
        player=player,
        game=game,
        value=value,
        target=target,
        _is_buy=True,
    )


def make_place(game: Game, player: Player, target: int = 4, value: int = BET) -> Wager:
    return Wager(
        definition=defs.PLACE_BET,
        player=player,
        game=game,
        value=value,
        target=target,
    )


def roll_result(game: Game, wager: Wager, total: int):
    return next(result for result in game.roll(total).wager_results if result.wager is wager)


# =======================
# DEFINITION / PLACEMENT
# =======================

def test_buy_uses_place_definition(buy_bet_game):
    game, player, wager = buy_bet_game
    assert wager.definition is defs.PLACE_BET
    assert wager.definition.wager_type is WagerType.PLACE_BET
    assert wager.is_buy is True
    assert wager.definition.remove_after_win is False
    assert wager.definition.can_turn_off is True

@pytest.mark.parametrize("target", [4, 5, 6, 8, 9, 10])
@pytest.mark.parametrize("point", [None, 6])
def test_explicit_buy_placement(buy_game, target, point):
    game, player = buy_game
    game._point = point
    wager = make_buy(game, player, target)
    game.place_wager(wager)
    assert wager in game.wagers
    assert wager.is_buy is True
    assert wager.collected_vig == 0
    assert player.bankroll == STARTING_BANKROLL - BET


@pytest.mark.parametrize("target", [None, 2, 3, 7, 11, 12])
def test_invalid_buy_target_rejected(buy_game, target):
    game, player = buy_game
    wager = make_buy(game, player, target=target)
    with pytest.raises(ValueError):
        game.place_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == STARTING_BANKROLL


def test_duplicate_buy_and_place_rejected(buy_bet_game):
    game, player, first = buy_bet_game
    second = make_place(game, player, target=4)
    with pytest.raises(GameRuleViolation):
        game.place_wager(second)
    assert first in game.wagers
    assert second not in game.wagers
    assert player.bankroll == STARTING_BANKROLL - BET


# =======================
# RESOLUTION AND PAYOUT
# =======================

@pytest.mark.parametrize("target", [4, 5, 6, 8, 9, 10])
def test_buy_wins_on_target(buy_game, target):
    game, player = buy_game
    wager = make_buy(game, player, target)
    game.place_wager(wager)
    result = roll_result(game, wager, target)
    assert result.resolution is Resolution.WIN
    assert wager in game.wagers


@pytest.mark.parametrize("target", [4, 5, 6, 8, 9, 10])
def test_buy_loses_on_seven(buy_game, target):
    game, player = buy_game
    wager = make_buy(game, player, target)
    game.place_wager(wager)
    result = roll_result(game, wager, 7)
    assert result.resolution is Resolution.LOSE
    assert wager not in game.wagers
    assert player.bankroll == STARTING_BANKROLL - BET


@pytest.mark.parametrize("roll", [2, 3, 5, 6, 8, 9, 10, 11, 12])
def test_buy_no_decision(buy_bet_game, roll):
    game, player, wager = buy_bet_game  # Buy 4
    result = roll_result(game, wager, roll)
    assert result.resolution is Resolution.NONE
    assert wager in game.wagers
    assert player.bankroll == STARTING_BANKROLL - BET


@pytest.mark.parametrize(
    "target, gross_profit",
    [(4, 200), (5, 150), (6, 120), (8, 120), (9, 150), (10, 200)],
)
@pytest.mark.parametrize("setting", [VigSetting.ON_WIN, VigSetting.UP_FRONT])
def test_buy_payout_and_commission(buy_game, target, gross_profit, setting):
    game, player = buy_game
    new_settings = replace(
        game.settings,
        buy_vig_setting=setting,
    )
        
    game._settings = new_settings
    wager = make_buy(game, player, target)
    game.place_wager(wager)

    vig = 5  # 5% of $100 Buy amount
    initial_vig = vig if setting is VigSetting.UP_FRONT else 0
    assert wager.collected_vig == initial_vig
    assert player.bankroll == STARTING_BANKROLL - BET - initial_vig

    result = roll_result(game, wager, target)
    assert result.resolution is Resolution.WIN
    assert result.profit == gross_profit - vig
    assert player.bankroll == STARTING_BANKROLL - BET - initial_vig + result.profit
    assert wager in game.wagers
    assert wager.collected_vig == initial_vig


@pytest.mark.parametrize("setting", [VigSetting.ON_WIN, VigSetting.UP_FRONT])
def test_buy_can_be_turned_off(setting, buy_game):
    game, player = buy_game
    new_settings = replace(
        game.settings,
        buy_vig_setting=setting,
    )
        
    game._settings = new_settings
    wager = make_buy(game, player)
    game.place_wager(wager)
    bankroll_before = player.bankroll
    vig_before = wager.collected_vig

    wager.is_working = False
    for total in (4, 7):
        result = roll_result(game, wager, total)
        assert result.resolution is Resolution.NONE
        assert wager in game.wagers
    assert player.bankroll == bankroll_before
    assert wager.collected_vig == vig_before

    wager.is_working = True
    assert roll_result(game, wager, 4).resolution is Resolution.WIN


# =======================
# UPFRONT VIG ADJUSTMENTS
# =======================

@pytest.fixture
def upfront_buy_game(game_setup):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        buy_vig_setting=VigSetting.UP_FRONT,
    )
        
    game._settings = new_settings
    wager = make_buy(game, player)
    game.place_wager(wager)
    return game, player, wager


def test_upfront_vig_collected_on_placement(upfront_buy_game):
    game, player, wager = upfront_buy_game
    assert wager.collected_vig == 5
    assert player.bankroll == 1395


def test_upfront_buy_increase_collects_difference(upfront_buy_game):
    game, player, wager = upfront_buy_game
    game.increase_wager(wager, 100)  # $100 -> $200; vig $5 -> $10
    assert wager.value == 200
    assert wager.collected_vig == 10
    assert player.bankroll == 1290


def test_upfront_buy_decrease_refunds_difference(upfront_buy_game):
    game, player, wager = upfront_buy_game
    game.decrease_wager(wager, 40)  # $100 -> $60; vig $5 -> $3
    assert wager.value == 60
    assert wager.collected_vig == 3
    assert player.bankroll == 1437


def test_upfront_buy_take_down_refunds_principal_and_vig(upfront_buy_game):
    game, player, wager = upfront_buy_game
    game.take_down_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == STARTING_BANKROLL


def test_upfront_buy_decrease_to_zero_refunds_all(upfront_buy_game):
    game, player, wager = upfront_buy_game
    game.decrease_wager(wager, BET)
    assert wager not in game.wagers
    assert player.bankroll == STARTING_BANKROLL


# =======================
# MANUAL CONVERSION
# =======================

def test_convert_place_to_upfront_buy_collects_vig(game_setup):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        buy_vig_setting=VigSetting.UP_FRONT,
    )
        
    game._settings = new_settings
    wager = make_place(game, player)
    game.place_wager(wager)
    assert wager.is_buy is False
    assert wager.collected_vig == 0

    game.set_wager_buy_status(wager, True)
    assert wager.is_buy is True
    assert wager.collected_vig == 5
    assert player.bankroll == 1395


def test_convert_upfront_buy_to_place_refunds_vig(upfront_buy_game):
    game, player, wager = upfront_buy_game
    game.set_wager_buy_status(wager, False)
    assert wager.is_buy is False
    assert wager.collected_vig == 0
    assert player.bankroll == 1400


def test_round_trip_conversion_no_vig_leak(upfront_buy_game):
    game, player, wager = upfront_buy_game
    game.set_wager_buy_status(wager, False)
    game.set_wager_buy_status(wager, True)
    assert wager.is_buy is True
    assert wager.collected_vig == 5
    assert player.bankroll == 1395
    game.take_down_wager(wager)
    assert player.bankroll == STARTING_BANKROLL


# =======================
# AUTO BUY
# =======================

def test_auto_buy_threshold(game_setup):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        buy_vig_setting=VigSetting.AUTO_BUY,
    )
        
    game._settings = new_settings
    threshold = game.settings.auto_buy_level
    assert threshold > 1

    below = make_place(game, player, target=4, value=threshold - 1)
    at = make_place(game, player, target=10, value=threshold)
    other = make_place(game, player, target=6, value=threshold)

    game.place_wager(below)
    game.place_wager(at)
    game.place_wager(other)
    assert below.is_buy is False
    assert at.is_buy is True
    assert other.is_buy is False
    assert all(w.collected_vig == 0 for w in (below, at, other))


def test_auto_buy_changes_with_wager_value(game_setup):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        buy_vig_setting=VigSetting.AUTO_BUY,
    )
        
    game._settings = new_settings
    threshold = game.settings.auto_buy_level
    assert threshold > 1

    wager = make_place(game, player, target=4, value=threshold - 1)
    game.place_wager(wager)
    assert wager.is_buy is False

    game.increase_wager(wager, 1)
    assert wager.value == threshold
    assert wager.is_buy is True
    assert wager.collected_vig == 0

    game.decrease_wager(wager, 1)
    assert wager.is_buy is False
    assert wager.collected_vig == 0
    assert player.bankroll == STARTING_BANKROLL - (threshold - 1)


def test_auto_buy_win_uses_buy_payout_and_on_win_vig(game_setup):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        buy_vig_setting=VigSetting.AUTO_BUY,
    )
        
    game._settings = new_settings
    value = max(100, game.settings.auto_buy_level)
    wager = make_place(game, player, target=4, value=value)
    game.place_wager(wager)
    assert wager.is_buy is True
    assert wager.collected_vig == 0

    result = roll_result(game, wager, 4)
    assert result.resolution is Resolution.WIN
    assert result.profit == 2 * value - game.calculate_vig(wager)
    assert wager.collected_vig == 0



# =======================
# LIFECYCLES
# =======================

def test_on_win_buy_lifecycle(buy_bet_game):
    game, player, wager = buy_bet_game
    assert player.bankroll == 1400
    assert wager.collected_vig == 0

    result = roll_result(game, wager, 4)
    assert result.profit == 195
    assert player.bankroll == 1595
    assert wager in game.wagers

    result = roll_result(game, wager, 4)
    assert result.profit == 195
    assert player.bankroll == 1790

    game.take_down_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1890  # Net two wins of $195 each


def test_upfront_buy_two_wins_then_take_down(upfront_buy_game):
    game, player, wager = upfront_buy_game
    assert player.bankroll == 1395
    assert wager.collected_vig == 5

    for expected_bankroll in (1590, 1785):
        result = roll_result(game, wager, 4)
        assert result.resolution is Resolution.WIN
        assert result.profit == 195
        assert player.bankroll == expected_bankroll
        assert wager.collected_vig == 5
        assert wager in game.wagers

    game.take_down_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1890  # Principal + unearned renewed vig refunded


def test_upfront_buy_loss_consumes_vig(upfront_buy_game):
    game, player, wager = upfront_buy_game
    result = roll_result(game, wager, 7)
    assert result.resolution is Resolution.LOSE
    assert wager not in game.wagers
    assert player.bankroll == 1395
