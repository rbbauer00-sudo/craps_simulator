
import pytest
from dataclasses import replace

from craps_engine import wager_definitions as defs
from craps_engine import constants as const
from craps_engine.game import Game
from craps_engine.player import Player
from craps_engine.wager import Wager
from craps_engine.enums import Resolution, WagerType, VigSetting
from craps_engine.exceptions import GameRuleViolation


TEST_WAGER_DEF = defs.PLACE_BET
TEST_WAGER_TYPE = WagerType.PLACE_BET
TEST_WAGER_NAME = "Place"
TEST_WAGER_VALUE = 60

@pytest.fixture
def place_game(game_setup):
    game, player = game_setup
    new_settings = replace(
        game.settings,
        buy_vig_setting = VigSetting.ON_WIN, 
    )
    game._settings = new_settings
    return game, player


@pytest.fixture
def place_bet_game(place_game) -> tuple[Game, Player, Wager]:
    game, player = place_game

    # Disable automatic Buy conversion for this suite.
    new_settings = replace(
        game.settings,
        buy_vig_setting = VigSetting.ON_WIN, 
    )
    game._settings = new_settings

    wager = Wager(
        definition=TEST_WAGER_DEF,
        player=player,
        game=game,
        value=TEST_WAGER_VALUE,
        target=6,
    )

    game.place_wager(wager)

    return game, player, wager


def get_result(game: Game, wager: Wager, roll: int):
    """Roll dice and return the result for the given wager."""
    return next(
        result
        for result in game.roll(roll).wager_results
        if result.wager is wager
    )

# =======================
# DEFINITION TESTS
# =======================

def test_wager_definition():
    wager_def = TEST_WAGER_DEF

    assert wager_def.wager_type is TEST_WAGER_TYPE
    assert wager_def.name == TEST_WAGER_NAME
    assert wager_def.remove_after_win is False
    assert wager_def.can_turn_off is True


# =======================
# PLACEMENT TESTS
# =======================

@pytest.mark.parametrize("target", sorted(const.BOX_NUMS))
@pytest.mark.parametrize("point", [None, 6])
def test_place_bet_placement_valid(
    place_game, target, point
):
    game, player = place_game
    #game.settings.buy_vig_setting = VigSetting.ON_WIN
    game._point = point

    wager = Wager(
        definition=TEST_WAGER_DEF,
        player=player,
        game=game,
        value=TEST_WAGER_VALUE,
        target=target,
    )

    game.place_wager(wager)

    assert wager in game.wagers
    assert wager.value == TEST_WAGER_VALUE
    assert player.bankroll == 1500 - TEST_WAGER_VALUE
    assert wager.collected_vig == 0
    assert wager.is_buy is False


@pytest.mark.parametrize(
    "target",
    [None, 2, 3, 7, 11, 12, 13]
)
def test_place_bet_invalid_target(place_game, target):
    game, player = place_game

    wager = Wager(
        definition=TEST_WAGER_DEF,
        player=player,
        game=game,
        value=TEST_WAGER_VALUE,
        target=target,
    )

    with pytest.raises(ValueError):
        game.place_wager(wager)

    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_place_bet_duplicate_rejection(place_bet_game):
    game, player, wager = place_bet_game

    second_wager = Wager(
        definition=TEST_WAGER_DEF,
        player=player,
        game=game,
        value=TEST_WAGER_VALUE,
        target=6,
    )

    with pytest.raises(GameRuleViolation):
        game.place_wager(second_wager)

    assert second_wager not in game.wagers
    assert wager in game.wagers
    assert player.bankroll == 1500 - TEST_WAGER_VALUE


def test_place_bet_different_targets_allowed(place_bet_game):
    game, player, wager = place_bet_game

    second_wager = Wager(
        definition=TEST_WAGER_DEF,
        player=player,
        game=game,
        value=TEST_WAGER_VALUE,
        target=8,
    )

    game.place_wager(second_wager)

    assert wager in game.wagers
    assert second_wager in game.wagers
    assert len(game.wagers) == 2
    assert player.bankroll == 1500 - 2 * TEST_WAGER_VALUE


def test_place_bet_incorrect_game_rejected(place_game):
    game, player = place_game
    other_game = Game()

    wager = Wager(
        definition=TEST_WAGER_DEF,
        player=player,
        game=other_game,
        value=TEST_WAGER_VALUE,
        target=6,
    )

    with pytest.raises(ValueError):
        game.place_wager(wager)

    assert wager not in game.wagers
    assert player.bankroll == 1500


# =======================
# RESOLUTION TESTS
# =======================

@pytest.mark.parametrize("target", sorted(const.BOX_NUMS))
def test_place_bet_win_on_target(place_game, target):
    game, player = place_game
    new_settings = replace(
        game.settings,
        buy_vig_setting = VigSetting.ON_WIN, 
    )
    game._settings = new_settings

    wager = Wager(
        definition=TEST_WAGER_DEF,
        player=player,
        game=game,
        value=TEST_WAGER_VALUE,
        target=target,
    )
    game.place_wager(wager)

    result = get_result(game, wager, target)

    assert result.resolution is Resolution.WIN


@pytest.mark.parametrize("target", sorted(const.BOX_NUMS))
def test_place_bet_lose_on_seven(place_game, target):
    game, player = place_game
    new_settings = replace(
        game.settings,
        buy_vig_setting = VigSetting.ON_WIN, 
    )
    game._settings = new_settings

    wager = Wager(
        definition=TEST_WAGER_DEF,
        player=player,
        game=game,
        value=TEST_WAGER_VALUE,
        target=target,
    )
    game.place_wager(wager)

    result = get_result(game, wager, 7)

    assert result.resolution is Resolution.LOSE


@pytest.mark.parametrize(
    "roll",
    [2, 3, 4, 5, 8, 9, 10, 11, 12]
)
def test_place_bet_no_resolution(place_bet_game, roll):
    game, player, wager = place_bet_game

    result = get_result(game, wager, roll)

    assert result.resolution is Resolution.NONE
    assert wager in game.wagers
    assert player.bankroll == 1500 - TEST_WAGER_VALUE


# =======================
# PAYOUT TESTS
# =======================

@pytest.mark.parametrize(
    "target, expected_profit",
    [
        (4, 108),   # 9:5
        (5, 84),    # 7:5
        (6, 70),    # 7:6
        (8, 70),    # 7:6
        (9, 84),    # 7:5
        (10, 108),  # 9:5
    ]
)
def test_place_bet_payout(
    place_game, target, expected_profit
):
    game, player = place_game
    new_settings = replace(
        game.settings,
        buy_vig_setting = VigSetting.ON_WIN, 
    )
    game._settings = new_settings

    wager = Wager(
        definition=TEST_WAGER_DEF,
        player=player,
        game=game,
        value=TEST_WAGER_VALUE,
        target=target,
    )
    game.place_wager(wager)

    result = get_result(game, wager, target)

    assert result.resolution is Resolution.WIN
    assert result.profit == expected_profit
    assert player.bankroll == (
        1500 - TEST_WAGER_VALUE + expected_profit
    )


@pytest.mark.parametrize(
    "target, value, expected_profit",
    [
        (4, 1, 1),    # 1 * 9 // 5
        (5, 1, 1),    # 1 * 7 // 5
        (6, 1, 1),    # 1 * 7 // 6
        (6, 5, 5),    # 5 * 7 // 6
        (6, 7, 8),    # 7 * 7 // 6
        (4, 7, 12),   # 7 * 9 // 5
    ]
)
def test_place_bet_integer_payout(
    place_game, target, value, expected_profit
):
    game, player = place_game
    new_settings = replace(
        game.settings,
        buy_vig_setting = VigSetting.ON_WIN, 
    )
    game._settings = new_settings

    wager = Wager(
        definition=TEST_WAGER_DEF,
        player=player,
        game=game,
        value=value,
        target=target,
    )
    game.place_wager(wager)

    result = get_result(game, wager, target)

    assert result.profit == expected_profit


# =======================
# PERSISTENCE TESTS
# =======================

def test_place_bet_stays_up_after_win(place_bet_game):
    game, player, wager = place_bet_game

    result = get_result(game, wager, 6)

    assert result.resolution is Resolution.WIN
    assert wager in game.wagers
    assert wager.value == TEST_WAGER_VALUE
    assert wager.target == 6


def test_place_bet_removed_after_loss(place_bet_game):
    game, player, wager = place_bet_game

    result = get_result(game, wager, 7)

    assert result.resolution is Resolution.LOSE
    assert wager not in game.wagers
    assert player.bankroll == 1500 - TEST_WAGER_VALUE


# =======================
# WORKING STATUS TESTS
# =======================

def test_place_bet_can_turn_off(place_bet_game):
    game, player, wager = place_bet_game

    wager.is_working = False

    assert wager.is_working is False


@pytest.mark.parametrize("roll", [6, 7])
def test_place_bet_off_does_not_resolve(place_bet_game, roll):
    game, player, wager = place_bet_game

    wager.is_working = False

    result = get_result(game, wager, roll)

    assert result.resolution is Resolution.NONE
    assert wager in game.wagers
    assert player.bankroll == 1500 - TEST_WAGER_VALUE


def test_place_bet_reactivated(place_bet_game):
    game, player, wager = place_bet_game

    wager.is_working = False
    result = get_result(game, wager, 6)

    assert result.resolution is Resolution.NONE

    wager.is_working = True
    result = get_result(game, wager, 6)

    assert result.resolution is Resolution.WIN
    assert wager.is_working is True


# =======================
# ADJUSTMENT TESTS
# =======================

def test_place_bet_increase(place_bet_game):
    game, player, wager = place_bet_game

    game.increase_wager(wager, 30)

    assert wager.value == 90
    assert wager.collected_vig == 0
    assert player.bankroll == 1500 - 90


def test_place_bet_decrease(place_bet_game):
    game, player, wager = place_bet_game

    game.decrease_wager(wager, 30)

    assert wager.value == 30
    assert wager.collected_vig == 0
    assert player.bankroll == 1500 - 30


def test_place_bet_decrease_to_zero(place_bet_game):
    game, player, wager = place_bet_game

    game.decrease_wager(wager, TEST_WAGER_VALUE)

    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_place_bet_take_down(place_bet_game):
    game, player, wager = place_bet_game

    game.take_down_wager(wager)

    assert wager not in game.wagers
    assert player.bankroll == 1500



# =======================
# LIFECYCLE TEST
# =======================

def test_place_bet_lifecycle(place_bet_game):
    game, player, wager = place_bet_game

    # Place $60 on 6.
    assert player.bankroll == 1440
    assert wager in game.wagers

    # Roll 5: no decision.
    result = get_result(game, wager, 5)
    assert result.resolution is Resolution.NONE
    assert player.bankroll == 1440

    # Roll 6: win $70, wager remains up.
    result = get_result(game, wager, 6)
    assert result.resolution is Resolution.WIN
    assert result.profit == 70
    assert player.bankroll == 1510
    assert wager in game.wagers

    # Increase wager to $90.
    game.increase_wager(wager, 30)
    assert wager.value == 90
    assert player.bankroll == 1480

    # Roll 6: win $105.
    result = get_result(game, wager, 6)
    assert result.resolution is Resolution.WIN
    assert result.profit == 105
    assert player.bankroll == 1585

    # Turn wager off and roll 7.
    wager.is_working = False
    result = get_result(game, wager, 7)
    assert result.resolution is Resolution.NONE
    assert wager in game.wagers

    # Turn wager back on, roll 7, and lose.
    wager.is_working = True
    result = get_result(game, wager, 7)
    assert result.resolution is Resolution.LOSE
    assert wager not in game.wagers

    # Net profit = $70 + $105 - $90.
    assert player.bankroll == 1585
