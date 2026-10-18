"""Cross-wager, full-roll integration tests for the craps engine.

Uses the same game_setup fixture and Wager API as test_ats_bets.py and
 test_fire_bet.py.  All rolls go through Game.roll(), including point
transitions, contracts, payout execution and wager removal.

Assumed wager-definition names: PASS_LINE, COME, FIELD, ATS_SMALL,
ATS_TALL, ATS_ALL and FIRE_BET. Adjust aliases if your module differs.
"""

import pytest
from conftest import result_for

from engine import wager_definitions as defs
from engine.enums import Resolution
from engine.exceptions import GameRuleViolation
from engine.wager import Wager, WagerResult
from engine.game import Game


def place(game, player, definition, value=5, *, target=None):
    wager = Wager(
        game=game,
        player=player,
        definition=definition,
        value=value,
        target=target,
    )
    game.place_wager(wager)
    return wager


def resolve(
        game: Game, 
        total,
) -> list[WagerResult]:
    """Execute a real roll, materializing the results once."""
    return game.roll(total).wager_results



def assert_active(game, *wagers):
    assert all(wager in game.wagers for wager in wagers)


def assert_inactive(game, *wagers):
    assert all(wager not in game.wagers for wager in wagers)


def assert_no_orphan_odds(game):
    """An active wager with a parent must retain an active parent."""
    for wager in game.wagers:
        if wager.parent_wager is not None:
            assert wager.parent_wager in game.wagers


def test_comeout_seven_resolves_mixed_wagers_without_ending_shooter(game_setup):
    """Same seven: Pass wins, Field/ATS lose, Fire survives."""
    game, player = game_setup
    starting = player.bankroll

    pass_line = place(game, player, defs.PASS_LINE, 25)
    field = place(game, player, defs.FIELD, 5)
    small = place(game, player, defs.ATS_SMALL, 5)
    tall = place(game, player, defs.ATS_TALL, 5)
    all_bet = place(game, player, defs.ATS_ALL, 5)
    fire = place(game, player, defs.FIRE_BET, 5)

    assert player.bankroll == starting - 50
    results = resolve(game, 7)

    assert result_for(results, pass_line).resolution is Resolution.WIN
    assert result_for(results, pass_line).profit == 25
    assert result_for(results, field).resolution is Resolution.LOSE
    for wager in (small, tall, all_bet):
        assert result_for(results, wager).resolution is Resolution.LOSE
    assert result_for(results, fire).resolution is Resolution.NONE

    assert_active(game, fire)
    assert_inactive(game, field, small, tall, all_bet)
    assert fire.targets_hit == set()
    assert game.point is None
    # The shooter continues after a comeout seven.
    assert game.shooter_roll_count != 0
    assert_no_orphan_odds(game)

    # A fresh ATS attempt can begin after the seven; Fire cannot be rebooked.
    replacement = place(game, player, defs.ATS_SMALL, 5)
    assert replacement.targets_hit == set()
    assert replacement.contract_min is None
    with pytest.raises(GameRuleViolation):
        place(game, player, defs.FIRE_BET, 5)
    assert_active(game, fire, replacement)


def test_simultaneous_point_and_come_resolution_with_bonus_progress(game_setup):
    """Come bet travels, point is made, then Come wins on a later roll."""
    game, player = game_setup
    pass_line = place(game, player, defs.PASS_LINE, 25)
    small = place(game, player, defs.ATS_SMALL, 5)
    all_bet = place(game, player, defs.ATS_ALL, 5)
    fire = place(game, player, defs.FIRE_BET, 5)

    resolve(game, 4)  # Establish point 4; all contracts lock.
    assert game.point == 4
    assert small.contract_min == small.contract_max == 5
    assert fire.contract_min == fire.contract_max == 5

    come = place(game, player, defs.COME, 25)
    results = resolve(game, 6)  # Untravelled Come moves to 6.
    assert result_for(results, come).resolution is Resolution.MOVE
    assert come.target == 6
    assert_active(game, come)
    assert game.point == 4

    results = resolve(game, 4)  # Point 4 made; Come 6 remains.
    assert result_for(results, pass_line).resolution is Resolution.WIN
    assert result_for(results, come).resolution is Resolution.NONE
    assert game.point is None
    assert fire.targets_hit == {4}
    assert_active(game, come, small, all_bet, fire)

    results = resolve(game, 6)  # Come 6 wins on a comeout roll.
    assert result_for(results, come).resolution is Resolution.WIN
    assert result_for(results, come).profit == 25
    assert_inactive(game, come)
    assert game.point == 6  # Meanwhile this establishes a new table point.
    assert fire.targets_hit == {4}  # Establishing 6 is not MAKING it.

    resolve(game, 6)  # Make point 6.
    assert game.point is None
    assert fire.targets_hit == {4, 6}
    assert small.targets_hit == {4, 6}
    assert_no_orphan_odds(game)


def test_full_mixed_wager_lifecycle_four_point_fire_and_ats_small(game_setup):
    """A shooter makes four distinct points, hits Small, then sevens out.

    Track independent ATS sets; Fire records completed points (not mere
    rolled numbers); Pass Line continues through repeated point cycles.
    Assert exact bonus payouts and shooter reset on the final seven-out.
    """
    game, player = game_setup
    initial = player.bankroll
    # Begin with the bonus wagers only: comeout 2 and 3 would lose
    # a Pass Line wager, but they legitimately advance ATS progress.
    small = place(game, player, defs.ATS_SMALL, 5)
    tall = place(game, player, defs.ATS_TALL, 5)
    all_bet = place(game, player, defs.ATS_ALL, 5)
    fire = place(game, player, defs.FIRE_BET, 5)

    assert player.bankroll == initial - 20

    for total in [2, 3]:
        results = resolve(game, total)
        assert result_for(results, fire).resolution is Resolution.NONE
        assert game.point is None
    assert small.targets_hit == {2, 3}
    assert fire.targets_hit == set()

    # Now add Pass Line before the first point is established.
    pass_line = place(game, player, defs.PASS_LINE, 25)
    assert player.bankroll == initial - 45

    # Make four DIFFERENT points; 6 also completes the Small ATS set.
    expected_progress = [({4}, 4), ({4, 5}, 5), ({4, 5, 6}, 6), ({4, 5, 6, 8}, 8)]
    small_result = None
    for points_made, point in expected_progress:
        established = resolve(game, point)
        assert game.point == point
        assert result_for(established, fire).resolution is Resolution.NONE
        assert fire.targets_hit == points_made - {point}

        # ATS counts every rolled total, not just points made. The
        # comeout 6 completes Small before the table point is made.
        if point == 6:
            small_result = result_for(established, small)
            assert small_result.resolution is Resolution.WIN
            assert small_result.profit == 5 * 35
            assert_inactive(game, small)

        made = resolve(game, point)
        assert game.point is None
        assert result_for(made, pass_line).resolution is Resolution.WIN
        assert fire.targets_hit == points_made
        assert result_for(made, fire).resolution is Resolution.NONE
        assert_no_orphan_odds(game)

    assert small_result is not None
    assert_active(game, fire, tall, all_bet)
    assert fire.targets_hit == {4, 5, 6, 8}
    assert tall.targets_hit == {8}
    assert all_bet.targets_hit == {2, 3, 4, 5, 6, 8}

    # Establish 9, but don't make it. Seven-out ends the Fire hand.
    resolve(game, 9)
    assert game.point == 9
    assert fire.targets_hit == {4, 5, 6, 8}
    results = resolve(game, 7)
    assert result_for(results, fire).resolution is Resolution.WIN
    assert result_for(results, fire).profit == 5 * 24
    assert result_for(results, tall).resolution is Resolution.LOSE
    assert result_for(results, all_bet).resolution is Resolution.LOSE
    assert result_for(results, pass_line).resolution is Resolution.LOSE
    assert_inactive(game, fire, tall, all_bet, pass_line)
    assert game.point is None
    assert game.shooter_roll_count == 0
    assert_no_orphan_odds(game)

    # Exactly 4 pass-line point wins, one pass-line loss, and two bonus wins:
    # PL net = +4*25 - 25; Small = +175 - 5 already at stake;
    # Fire = +120 - 5 already at stake; Tall and All lose $5 each.
    expected_net = 4 * 25 - 25 + 5 * 35 + 5 * 24 - 5 - 5
    assert player.bankroll == initial + expected_net

    # New shooter starts with clean bonus histories and unlocked contracts.
    next_fire = place(game, player, defs.FIRE_BET, 5)
    next_small = place(game, player, defs.ATS_SMALL, 5)
    assert next_fire.targets_hit == set()
    assert next_small.targets_hit == set()
    assert next_fire.contract_min is None
    assert next_small.contract_min is None
