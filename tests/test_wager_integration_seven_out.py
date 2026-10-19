"""Multi-player, mixed-wager seven-out integration test.

Run: pytest tests/test_wager_integration_seven_out.py -v

Uses the same Wager(game=...), game_setup, and Game.roll(total) API as
existing integration tests. Definition names for Don't/odds vary between
engines: adjust the aliases in ``definition()`` if yours differ.

An important premise: a player can hold Don't Pass while ANOTHER player
holds Pass Line, even if allow_doey_dont=False (that setting should be
per-player rather than a table-wide prohibition).
"""

import pytest
from conftest import result_for

from engine import defs, Wager, WagerResult, Game, Resolution

def definition(*names):
    for name in names:
        found = getattr(defs, name, None)
        if found is not None:
            return found
    pytest.fail(f"Missing wager definition; expected one of: {', '.join(names)}")


def place(game, player, wager_def, amount=25, *, target=None, parent=None):
    wager = Wager(
        game=game,
        player=player,
        definition=wager_def,
        value=amount,
        target=target,
        parent_wager=parent,
    )
    game.place_wager(wager)
    return wager


def roll(
    game: Game, 
    total,
) -> list[WagerResult]:
    return game.roll(total).wager_results


def assert_no_orphan_children(game):
    for wager in game.wagers:
        if wager.parent_wager is not None:
            assert wager.parent_wager in game.wagers


def test_opposing_players_travelled_bets_and_odds_on_seven_out(game_setup):
    """The same seven resolves opposite sides differently without mixing accounts.

    Player A: Pass + Pass odds + travelled Come + Come odds + Field.
    Player B: Don't Pass + travelled Don't Come + ATS Small + Fire.

    Timeline: establish 4; Come travels to 6; Don't Come travels to 5;
    seven-out with point 4 still on. Result: all A's bets lose, B's
    Don't-side wagers win, while ATS and Fire lose. All odds/parents clean up.
    """
    game, player_a = game_setup
    player_b = game.add_player()
    start_a, start_b = player_a.bankroll, player_b.bankroll

    pass_line = place(game, player_a, defs.PASS_LINE, 25)
    dont_pass = place(
        game, player_b, definition("DONT_PASS", "DONT_PASS_LINE"), 25
    )
    small = place(game, player_b, defs.ATS_SMALL, 5)
    fire = place(game, player_b, defs.FIRE_BET, 5)

    first = roll(game, 4)  # Point ON; no one has won yet.
    assert game.point == 4
    for wager in (pass_line, dont_pass, small, fire):
        assert result_for(first, wager).resolution is Resolution.NONE

    pass_odds = place(
        game, player_a,
        definition("PASS_LINE_ODDS", "LINE_ODDS", "PASS_ODDS"),
        10, parent=pass_line,
    )
    come = place(game, player_a, defs.COME, 25)
    # Place Don't Come only after Come has travelled, so each receives
    # a different established number.

    six = roll(game, 6)
    assert result_for(six, come).resolution is Resolution.MOVE
    assert come.target == 6
    assert game.point == 4

    dont_come = place(game, player_b, definition("DONT_COME", "DC"), 25)
    five = roll(game, 5)
    assert result_for(five, dont_come).resolution is Resolution.MOVE
    assert dont_come.target == 5
    assert result_for(five, come).resolution is Resolution.NONE
    assert game.point == 4

    come_odds = place(
        game, player_a,
        definition("COME_ODDS", "LINE_ODDS", "ODDS"),
        10, parent=come,
    )
    # Field bet is a one-roll wager, so place it ONLY immediately before 7.
    field = place(game, player_a, defs.FIELD, 5)

    assert_no_orphan_children(game)
    assert small.targets_hit == {4, 5, 6}
    assert fire.targets_hit == set()  # No points have been MADE.

    # All wagers on this roll are known; bankroll effects are checked using
    # a complete profit/stake ledger rather than hard-coded odds payouts.
    before_a, before_b = player_a.bankroll, player_b.bankroll
    active_before = list(game.wagers)
    assert set(active_before) == {
        pass_line, dont_pass, small, fire, pass_odds,
        come, dont_come, come_odds, field,
    }

    results = roll(game, 7)
    expected = {
        pass_line: Resolution.LOSE,
        pass_odds: Resolution.LOSE,
        come: Resolution.LOSE,
        come_odds: Resolution.LOSE,
        field: Resolution.LOSE,
        dont_pass: Resolution.WIN,
        dont_come: Resolution.WIN,
        small: Resolution.LOSE,
        fire: Resolution.LOSE,
    }
    for wager, outcome in expected.items():
        assert result_for(results, wager).resolution is outcome

    # For wagers removed on a win, stake is returned in addition to profit.
    # All of the wagers here have a WIN or LOSE resolution on seven-out.
    # An open Don't Pass/Don't Come winning position must be removed.
    assert set(game.wagers) == {dont_pass}
    assert game.point is None
    assert game.shooter_roll_count == 0
    assert_no_orphan_children(game)

    # Avoid assuming a particular Don't-side odds payout convention: profit
    # should agree with the actual result objects, and winning stakes returned.
    # NOTE: this engine reports profit only, not returned stake.
    for player, before in (
    (player_a, before_a),
    (player_b, before_b),
    ):
        player_results = [
            r for r in results
            if r.wager.player is player
        ]

        returned_stakes = sum(
            r.wager.value
            for r in player_results
            if (
                r.resolution is Resolution.WIN
                and r.wager not in game.wagers
            )
        )

        profit = sum(
            r.profit
            for r in player_results
        )

        assert player.bankroll == (
            before + returned_stakes + profit
        )

        # Player A lost every wager; B's Don't-side gains offset the lost bonuses.
        assert player_a.bankroll < start_a
        assert player_b.bankroll > start_b - 10

    # A new shooter can begin with a fresh wager; previous ATS/Fire state
    # should never leak into the next shooter.
    new_small = place(game, player_b, defs.ATS_SMALL, 5)
    new_fire = place(game, player_b, defs.FIRE_BET, 5)
    assert new_small.targets_hit == set()
    assert new_fire.targets_hit == set()
    assert new_small.contract_min is None
    assert new_fire.contract_min is None
