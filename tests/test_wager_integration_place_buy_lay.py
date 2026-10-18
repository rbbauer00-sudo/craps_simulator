"""Multi-player Place / Buy / Lay / Hardway / Field lifecycle integration.

Run: pytest tests/test_wager_integration_place_buy_lay.py -v

Matches the integration test convention: game_setup -> (game, player),
Wager(game=...), game.roll(total), and identity-based Wager objects.

Two compatibility points are deliberately centralized below:
  * Definitions may call place/buy/lay bets by different names.
  * Some engines implement Buy as an `is_buy` mode of Place.
Adjust `place_number()` / `buy_number()` / `lay_number()` if your
existing place/buy/lay tests use another constructor convention.

The wager amounts chosen are multiples suited to conventional payouts.
Tests assert resolutions, persistence, independence and conservation on
rolls without vig settlements, rather than assume vig-on-win vs upfront.
"""

import pytest
from conftest import result_for

from engine import wager_definitions as defs
from engine.enums import Resolution
from engine.wager import Wager, WagerResult
from engine.game import Game


def definition(*names):
    for name in names:
        found = getattr(defs, name, None)
        if found is not None:
            return found
    pytest.fail(f"Missing wager definition (tried {', '.join(names)})")


def place(game, player, wager_def, value, *, target=None, is_buy=None):
    wager = Wager(
        game=game, player=player, definition=wager_def,
        value=value, target=target,
    )
    if is_buy is not None:
        # Your Wager supports the `_is_buy` mode; set it *before* placement.
        # If your public API now has a mode-switch method, use it here instead.
        wager._is_buy = is_buy
    game.place_wager(wager)
    return wager


def place_number(game, player, target, value):
    return place(game, player, definition("PLACE", "PLACE_BET"), value, target=target)


def buy_number(game, player, target, value):
    buy_def = getattr(defs, "BUY", None) or getattr(defs, "BUY_BET", None)
    if buy_def is not None:
        return place(game, player, buy_def, value, target=target)
    return place(game, player, definition("PLACE", "PLACE_BET"), value,
                 target=target, is_buy=True)


def lay_number(game, player, target, value):
    return place(game, player, definition("LAY", "LAY_BET"), value, target=target)


def hard_six(game, player, value):
    return place(game, player, definition("HARDWAY", "HARDWAYS", "HARD_6", "HARD_SIX"),
                 value, target=6)


def roll(
    game: Game, 
    total,
) -> list[WagerResult]:
    return game.roll(total).wager_results



def assert_active(game, *wagers):
    for wager in wagers:
        assert wager in game.wagers, f"Unexpectedly removed: {wager.definition.name}"


def assert_inactive(game, *wagers):
    for wager in wagers:
        assert wager not in game.wagers, f"Unexpectedly active: {wager.definition.name}"


def assert_no_orphans(game):
    for wager in game.wagers:
        if wager.parent_wager is not None:
            assert wager.parent_wager in game.wagers


def test_mixed_place_buy_lay_hardway_field_two_players(game_setup):
    """A point-5 hand: soft 6, buy 10, then seven-out.

    A owns Place 6 and Hard 6; B owns Buy 10, Lay 4 and Field.
    This tests coexistence, independent bankrolls, and a mixed seven-out.
    """
    game, a = game_setup
    b = game.add_player()
    start_a, start_b = a.bankroll, b.bankroll

    roll(game, 5)  # Point on; no wagers yet.
    assert game.point == 5

    place6 = place_number(game, a, 6, 30)
    hard6 = hard_six(game, a, 5)
    buy10 = buy_number(game, b, 10, 20)
    lay4 = lay_number(game, b, 4, 40)
    field = place(game, b, defs.FIELD, 5)
    assert_active(game, place6, hard6, buy10, lay4, field)
    assert len(game.wagers) == 5
    assert a.bankroll == start_a - 35
    # Buy/Lay may charge vig on placement; don't hardcode B's bankroll.
    assert b.bankroll <= start_b - 65
    assert_no_orphans(game)

    before_a, before_b = a.bankroll, b.bankroll
    results = roll(game, 6)  # Soft/hard distinction doesn't matter for Place 6.
    assert result_for(results, place6).resolution is Resolution.WIN
    assert result_for(results, place6).profit == 35  # $30 pays 7:6
    # A total-only predetermined 6 does not prove hard vs easy dice.
    # Check hardway's loss in the explicit (2, 4) test below.
    assert result_for(results, buy10).resolution is Resolution.NONE
    assert result_for(results, lay4).resolution is Resolution.NONE
    assert result_for(results, field).resolution is Resolution.LOSE
    assert a.bankroll >= before_a + 35
    assert b.bankroll == before_b
    assert_inactive(game, field)
    assert_active(game, place6, buy10, lay4)
    assert game.point == 5
    assert_no_orphans(game)

    # Buy 10 wins and can stay up; Lay 4 is unaffected.
    results = roll(game, 10)
    assert result_for(results, buy10).resolution is Resolution.WIN
    assert result_for(results, lay4).resolution is Resolution.NONE
    assert game.point == 5
    assert_active(game, lay4)
    assert_no_orphans(game)

    # Seven-out kills active place/buy/hardways, but makes the Lay 4 win.
    active_before = list(game.wagers)
    before_b = b.bankroll
    results = roll(game, 7)
    assert result_for(results, lay4).resolution is Resolution.WIN
    assert result_for(results, place6).resolution is Resolution.LOSE
    if hard6 in active_before:
        assert result_for(results, hard6).resolution is Resolution.LOSE
    if buy10 in active_before:
        assert result_for(results, buy10).resolution is Resolution.LOSE
    assert b.bankroll > before_b  # Lay profits; settlement may retain stake.
    assert_inactive(game, place6, hard6)
    assert game.point is None
    assert game.shooter_roll_count == 0
    assert_no_orphans(game)


def test_place_and_hardway_resolve_differently_on_soft_six(game_setup):
    """The same roll wins Place 6 but loses Hard 6 (2+4)."""
    game, a = game_setup
    b = game.add_player()
    roll(game, 5)
    place6 = place_number(game, a, 6, 30)
    hard6 = hard_six(game, b, 5)

    # If Game.roll accepts the Dice object's tuple predetermined-roll API,
    # the exact faces let us test the distinction, rather than just total 6.
    results = game.roll(2, 4).wager_results
    assert result_for(results, place6).resolution is Resolution.WIN
    assert result_for(results, hard6).resolution is Resolution.LOSE
    assert_active(game, place6)
    assert_inactive(game, hard6)
    assert game.point == 5
    assert_no_orphans(game)
