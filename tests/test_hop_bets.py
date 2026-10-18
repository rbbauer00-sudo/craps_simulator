
import pytest
from conftest import result_for

from engine import wager_definitions as defs
from engine import constants as const
from engine.dice import RollResult
from engine.enums import Resolution, WagerType
from engine.exceptions import GameRuleViolation, InsufficientFundsError
from engine.game import Game
from engine.player import Player
from engine.wager import Wager


DEF = defs.HOP_BET
STAKE = 5
HopGame = tuple[Game, Player, Wager]


@pytest.fixture
def hop_game(game_setup) -> HopGame:
    game, player = game_setup
    wager = Wager(
        definition=DEF, 
        player=player,
        game=game, 
        value=STAKE, 
        target=(2, 3),
    )

    game.place_wager(wager)
    return game, player, wager



# ============================ DEFINITION ============================

def test_hop_definition():
    assert DEF.wager_type is WagerType.HOP
    assert DEF.can_turn_off is False


def test_hop_cannot_turn_off(hop_game):
    _, _, wager = hop_game
    with pytest.raises(GameRuleViolation):
        wager.is_working = False
    assert wager.is_working is True


# ============================= PLACEMENT ============================

@pytest.mark.parametrize('point', [None, 4, 6, 10])
def test_hop_placeable_regardless_of_table_point(game_setup, point):
    game, player = game_setup
    game._point = point
    wager = Wager(
        definition=DEF, 
        player=player,
        game=game, 
        value=STAKE, 
        target=(2, 3),
    )

    game.place_wager(wager)
    assert wager in game.wagers
    assert player.bankroll == 1500 - STAKE


hop_ids = [str(target) for target in const.HOP_TARGETS]

@pytest.mark.parametrize('target', const.HOP_TARGETS, ids=hop_ids)
def test_various_hop_targets_can_be_placed(game_setup, target):
    game, player = game_setup
    wager = Wager(
        definition=DEF, 
        player=player,
        game=game, 
        value=STAKE, 
        target=target,
    )

    game.place_wager(wager)
    assert wager in game.wagers
    assert wager.target == target


def test_duplicate_hop_rejected_without_charging(hop_game):
    game, player, wager = hop_game
    before = player.bankroll
    duplicate = Wager(
        definition=DEF,
        player=player,
        game=game, 
        value=10, 
        target=wager.target,
    )

    with pytest.raises(GameRuleViolation):
        game.place_wager(duplicate)
    assert duplicate not in game.wagers
    assert wager in game.wagers
    assert player.bankroll == before


def test_different_hop_targets_can_coexist(hop_game):
    game, player, first = hop_game
    second = Wager(
        definition=DEF, 
        player=player,
        game=game, 
        value=10, 
        target=(3, 3),
    )

    game.place_wager(second)
    assert first in game.wagers and second in game.wagers
    assert player.bankroll == 1485


def test_different_players_same_target(hop_game):
    game, _, first = hop_game
    player2 = game.add_player()
    second = Wager(
        definition=DEF, 
        player=player2,
        game=game, 
        value=STAKE, 
        target=first.target,
    )

    game.place_wager(second)
    assert first in game.wagers and second in game.wagers


@pytest.mark.parametrize('value', [0, -1, -10])
def test_nonpositive_hop_rejected(game_setup, value):
    game, player = game_setup
    wager = Wager(
        definition=DEF, 
        player=player,
        game=game, 
        value=value, 
        target=(2, 3),
    )

    with pytest.raises((GameRuleViolation, ValueError)):
        game.place_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


def test_unaffordable_hop_rejected(game_setup):
    game, player = game_setup
    wager = Wager(
        definition=DEF, 
        player=player,
        game=game, 
        value=1501, 
        target=(2, 3),
    )

    with pytest.raises(InsufficientFundsError):
        game.place_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500


# ============================ RESOLUTION ============================

@pytest.mark.parametrize(
    "target",
    sorted(const.HOP_TARGETS),
)
def test_hop_exact_target_both_orders(
    game_setup,
    target,
):
    game, player = game_setup

    wager = Wager(
        definition=defs.HOP_BET,
        player=player,
        game=game,
        value=5,
        target=target,
    )
    game.place_wager(wager)

    d1, d2 = target

    for dice in ((d1, d2), (d2, d1)):
        result = game._get_single_wager_result(
            wager,
            RollResult(*dice),
        )

        assert result.resolution is Resolution.WIN


@pytest.mark.parametrize(
    "target, dice",
    [
        ((1, 4), (2, 3)),  # Both total 5
        ((1, 5), (2, 4)),  # Both total 6
        ((1, 6), (2, 5)),  # Both total 7
        ((2, 6), (3, 5)),  # Both total 8
        ((3, 6), (4, 5)),  # Both total 9
        ((4, 6), (5, 5)),  # Both total 10
    ],
)
def test_hop_same_total_different_combination_loses(
    game_setup,
    target,
    dice,
):
    game, player = game_setup

    wager = Wager(
        definition=defs.HOP_BET,
        player=player,
        game=game,
        value=5,
        target=target,
    )
    game.place_wager(wager)

    result = game._get_single_wager_result(
        wager,
        RollResult(*dice),
    )

    assert result.resolution is Resolution.LOSE



@pytest.mark.parametrize('target, dice', [
    ((2, 3), (1, 4)),  # same total, different combination
    ((2, 3), (1, 5)),  # different total
    ((3, 3), (2, 4)),  # same total, different combination
    ((4, 6), (5, 5)),  # same total, different combination
])
def test_hop_loses_on_any_other_combination(game_setup, target, dice):
    game, player = game_setup
    wager = Wager(
        definition=DEF, 
        player=player,
        game=game, 
        value=STAKE, 
        target=target,
    )

    game.place_wager(wager)
    result = game._get_single_wager_result(wager, game._dice.roll(*dice))
    assert result.resolution is Resolution.LOSE
    assert result.profit == 0


# ============================== PAYOUT ==============================

@pytest.mark.parametrize('target, expected_profit', [
    ((2, 3), 75),   # easy, 15:1
    ((1, 4), 75),
    ((4, 6), 75),
    ((3, 3), 150),  # hard, 30:1
    ((4, 4), 150),
    ((5, 5), 150),
])
def test_hop_payouts(game_setup, target, expected_profit):
    game, player = game_setup
    wager = Wager(
        definition=DEF, 
        player=player,
        game=game, 
        value=STAKE, 
        target=target,
    )

    game.place_wager(wager)
    result = game._get_single_wager_result(wager, game._dice.roll(*target))
    assert result.resolution is Resolution.WIN
    assert result.profit == expected_profit


@pytest.mark.parametrize('stake, expected', [(1, 15), (2, 30), (7, 105)])
def test_easy_hop_payout_scales_with_stake(game_setup, stake, expected):
    game, player = game_setup
    wager = Wager(
        definition=DEF, 
        player=player,
        game=game, 
        value=stake, 
        target=(2, 3),
    )

    game.place_wager(wager)
    result = game._get_single_wager_result(wager, game._dice.roll(3, 2))
    assert result.profit == expected


# ========================= PERSISTENCE / LIFECYCLE ===================

def test_losing_hop_comes_down_and_loses_stake(hop_game):
    game, player, wager = hop_game
    results = game.roll(1, 4).wager_results   # same total as (2, 3), different dice
    result = result_for(results, wager)
    assert result.resolution is Resolution.LOSE
    assert wager not in game.wagers
    assert player.bankroll == 1495


def test_winning_hop_pays_and_obeys_persistence_setting(hop_game):
    game, player, wager = hop_game
    results = game.roll(3, 2).wager_results
    result = result_for(results, wager)
    assert result.resolution is Resolution.WIN
    assert result.profit == 75
    assert player.bankroll == 1500 - STAKE + 75 + (
        0 if wager in game.wagers else STAKE
    )
    assert (wager not in game.wagers) is DEF.remove_after_win


def test_two_different_hops_can_resolve_on_same_roll(hop_game):
    game, player, winning = hop_game
    losing = Wager(
        definition=DEF, 
        player=player,
        game=game, 
        value=10, 
        target=(3, 3),
    )
    
    game.place_wager(losing)
    results = game.roll(2, 3).wager_results
    assert result_for(results, winning).resolution is Resolution.WIN
    assert result_for(results, losing).resolution is Resolution.LOSE
    assert losing not in game.wagers
    expected = 1500 - 5 - 10 + 75 + (0 if winning in game.wagers else 5)
    assert player.bankroll == expected


def test_hop_can_be_voluntarily_taken_down_and_refunded(hop_game):
    game, player, wager = hop_game
    game.take_down_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == 1500
