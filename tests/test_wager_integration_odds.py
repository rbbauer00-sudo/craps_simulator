"""Multi-wager integration: Pass Line/odds, Come, Field, and seven-out.

Run with: pytest tests/test_wager_integration_odds.py -v

Assumptions to check against your definitions:
- Pass Line odds definition is PASS_LINE_ODDS (aliases below).
- Odds are placed with parent_wager=<active parent>.
- Standard 3-4-5 odds: point 4 pays 2:1 and point 6 pays 6:5.
- Winning line odds are returned/removed after a point is made.
- Pass Line stays up after a win, without automatically rebooking odds.

These are integration tests: they exercise Game.roll() and real bankroll
accounting rather than calling payout or resolution helpers directly.
"""

import pytest
from conftest import result_for

from craps_engine import wager_definitions as defs
from craps_engine.enums import Resolution
from craps_engine.wager import Wager, WagerResult
from craps_engine.game import Game


def place(game, player, definition, value=25, *, parent=None):
    wager = Wager(
        game=game,
        player=player,
        definition=definition,
        value=value,
        parent_wager=parent,
    )
    game.place_wager(wager)
    return wager


def roll(
    game: Game, 
    total,
) -> list[WagerResult]:
    return game.roll(total).wager_results


def assert_no_orphan_odds(game):
    for wager in game.wagers:
        if wager.parent_wager is not None:
            assert wager.parent_wager in game.wagers


def line_odds_definition():
    """Adjust this lookup if your engine uses a different definition name."""
    for name in ("PASS_LINE_ODDS", "LINE_ODDS", "PASS_ODDS"):
        definition = getattr(defs, name, None)
        if definition is not None:
            return definition
    pytest.fail(
        "No Pass Line odds definition found: update line_odds_definition() "
        "to match your wager_definitions module."
    )


def test_pass_line_odds_field_win_together_then_seven_out(game_setup):
    """Point-4 win pays three wagers; later 7-out loses the remaining line."""
    game, player = game_setup
    starting = player.bankroll

    line = place(game, player, defs.PASS_LINE, 25)
    roll(game, 4)  # Establish point; do not yet pay line bet.
    assert game.point == 4
    assert line in game.wagers
    assert player.bankroll == starting - 25

    odds = place(game, player, line_odds_definition(), 10, parent=line)
    field = place(game, player, defs.FIELD, 5)
    assert player.bankroll == starting - 40

    results = roll(game, 4)  # Make point; Field 4 wins too.
    assert result_for(results, line).resolution is Resolution.WIN
    assert result_for(results, line).profit == 25
    assert result_for(results, odds).resolution is Resolution.WIN
    assert result_for(results, odds).profit == 20  # $10 odds pay 2:1 on 4
    assert result_for(results, field).resolution is Resolution.WIN
    assert result_for(results, field).profit == 5
    assert game.point is None
    assert line in game.wagers
    assert odds not in game.wagers
    # Field bets may stay up after a win in this engine; manually take down
    # for the next part of the scenario if necessary.
    assert_no_orphan_odds(game)
    # Pass Line stake remains posted; Field payout behavior depends on
    # whether its winning wager stays up. Clear it before accounting.
    if field in game.wagers:
        assert player.bankroll == starting + 20
        game.take_down_wager(field)
    else:
        assert player.bankroll == starting + 25
    assert player.bankroll == starting + 25

    # Remaining Pass Line is still at risk. Establish 6 then seven-out.
    results = roll(game, 6)
    assert result_for(results, line).resolution is Resolution.NONE
    assert game.point == 6
    results = roll(game, 7)
    assert result_for(results, line).resolution is Resolution.LOSE
    assert line not in game.wagers
    assert game.point is None
    assert game.shooter_roll_count == 0
    assert_no_orphan_odds(game)
    assert player.bankroll == starting + 25


def test_line_and_odds_both_lose_on_seven_out(game_setup):
    """Child and parent must both lose; no odds or original stake refunded."""
    game, player = game_setup
    starting = player.bankroll
    line = place(game, player, defs.PASS_LINE, 25)
    roll(game, 6)
    odds = place(game, player, line_odds_definition(), 10, parent=line)
    assert player.bankroll == starting - 35

    results = roll(game, 7)
    assert result_for(results, line).resolution is Resolution.LOSE
    assert result_for(results, odds).resolution is Resolution.LOSE
    assert line not in game.wagers
    assert odds not in game.wagers
    assert player.bankroll == starting - 35
    assert game.point is None
    assert game.shooter_roll_count == 0
    assert_no_orphan_odds(game)


def test_pass_line_odds_and_travelled_come_resolve_independently(game_setup):
    """The table point pays line+odds without prematurely removing Come 6."""
    game, player = game_setup
    line = place(game, player, defs.PASS_LINE, 25)
    roll(game, 4)
    odds = place(game, player, line_odds_definition(), 10, parent=line)
    come = place(game, player, defs.COME, 25)

    results = roll(game, 6)  # Come travels; table point remains 4.
    assert result_for(results, come).resolution is Resolution.MOVE
    assert come.target == 6
    assert game.point == 4
    assert_no_orphan_odds(game)

    results = roll(game, 4)  # Win Pass+odds; travelled Come 6 persists.
    assert result_for(results, line).resolution is Resolution.WIN
    assert result_for(results, odds).resolution is Resolution.WIN
    assert result_for(results, come).resolution is Resolution.NONE
    assert come in game.wagers
    assert odds not in game.wagers
    assert game.point is None
    assert_no_orphan_odds(game)

    results = roll(game, 6)  # Come wins even as table point establishes at 6.
    assert result_for(results, come).resolution is Resolution.WIN
    assert result_for(results, come).profit == 25
    assert come not in game.wagers
    assert game.point == 6
    assert_no_orphan_odds(game)
