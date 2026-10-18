"""Engine-wide invariants and controlled accounting tests.

Run: pytest tests/test_game_invariants.py -v

Designed for the established API:
  game_setup -> (game, player)
  game.add_player(), game.place_wager(Wager(...)), game.roll(d1, d2)
  game.point, game.shooter_roll_count, game.wagers, game.players

`assert_game_invariants` is intentionally reusable from future stress tests.
It checks *active* contracts only if the limits are not None, and never
assumes all WIN wagers come down. Accounting tests use bets with no vig.
"""

import pytest
from conftest import result_for

from craps_engine import wager_definitions as defs
from craps_engine.enums import Resolution
from craps_engine.wager import Wager, WagerResult
from craps_engine.game import Game


BOX_NUMBERS = {4, 5, 6, 8, 9, 10}


def place(game, player, definition, value=25, *, target=None, parent=None):
    wager = Wager(
        game=game,
        player=player,
        definition=definition,
        value=value,
        target=target,
        parent_wager=parent,
    )
    game.place_wager(wager)
    return wager


def roll(
        game: Game, 
        *dice: int,
) -> list[WagerResult]:
    return list(game.roll(*dice).wager_results)


def assert_game_invariants(game):
    """Validate current state after a completed engine operation.

    This intentionally does not assert that an active wager's contract is
    initialized, since contracts lock on *roll*, not on placement. It also
    does not require contracts to be immediately cleared on comeout: the
    engine may update them during the following roll.
    """
    assert game.point is None or game.point in BOX_NUMBERS
    assert isinstance(game.shooter_roll_count, int)
    assert game.shooter_roll_count >= 0

    active = list(game.wagers)
    assert len(active) == len({id(wager) for wager in active}), (
        "The same wager object appears more than once in game.wagers"
    )

    players = list(game.players)
    assert len(players) == len({id(player) for player in players})
    for player in players:
        assert isinstance(player.bankroll, int)
        assert player.bankroll >= 0, f"Negative bankroll: {player}"

    for wager in active:
        assert wager.game is game, "Active wager belongs to another game"
        assert any(wager.player is player for player in players), (
            "Active wager belongs to a player not in game.players"
        )
        assert isinstance(wager.value, int) and not isinstance(wager.value, bool)
        assert wager.value > 0, "Active wager has nonpositive stake"

        low = wager.contract_min
        high = wager.contract_max
        if low is not None:
            assert isinstance(low, int) and low >= 0
            assert wager.value >= low, "Wager reduced below contract minimum"
        if high is not None:
            assert isinstance(high, int) and high >= 0
            assert wager.value <= high, "Wager increased above contract maximum"
        if low is not None and high is not None:
            assert low <= high

        if wager.parent_wager is not None:
            assert any(parent is wager.parent_wager for parent in active), (
                "Orphaned child wager"
            )
            assert wager.parent_wager is not wager
            assert wager.parent_wager.player is wager.player
            assert wager.parent_wager.game is game

        if hasattr(wager, "targets_hit"):
            assert isinstance(wager.targets_hit, (set, frozenset))
            assert all(isinstance(n, int) and 2 <= n <= 12 for n in wager.targets_hit)


def assert_roll_accounting(game, before_bankrolls, results, *, vig_paid=None):
    """Check a completed roll with no stake adjustments or new placements.

    Assumptions: result.profit is net profit (not returned principal), every
    removed winning wager returns its stake, retained winners keep their stake,
    and there are no vig payments unless supplied via `vig_paid`.
    Use only for scenarios whose wager lifecycle follows these rules.
    """
    vig_paid = vig_paid or {}
    assert len(results) == len({id(r.wager) for r in results}), (
        "A wager produced more than one result on the same roll"
    )

    for player, before in before_bankrolls.items():
        owned = [r for r in results if r.wager.player is player]
        profits = sum(r.profit for r in owned)
        returned_principal = sum(
            r.wager.value for r in owned
            if r.resolution is Resolution.WIN
            and not any(w is r.wager for w in game.wagers)
        )
        expected = before + profits + returned_principal - vig_paid.get(player, 0)
        assert player.bankroll == expected, (
            f"Accounting mismatch for {player}: actual {player.bankroll}, "
            f"expected {expected} (profits={profits}, "
            f"returned_stakes={returned_principal})"
        )


def test_initial_game_state_and_multiple_players(game_setup):
    game, a = game_setup
    b = game.add_player()
    assert a is not b
    assert_game_invariants(game)
    assert not game.wagers
    assert game.point is None
    assert game.shooter_roll_count == 0


def test_placement_debits_each_player_and_locks_on_first_roll(game_setup):
    game, a = game_setup
    b = game.add_player()
    a_initial, b_initial = a.bankroll, b.bankroll

    passing = place(game, a, defs.PASS_LINE, 25)
    small = place(game, b, defs.ATS_SMALL, 5)
    fire = place(game, b, defs.FIRE_BET, 5)
    assert a.bankroll == a_initial - 25
    assert b.bankroll == b_initial - 10
    assert small.contract_min is None and small.contract_max is None
    assert fire.contract_min is None and fire.contract_max is None
    assert_game_invariants(game)

    results = roll(game, 4)  # Establish point; bonus wagers continue.
    assert result_for(results, passing).resolution is Resolution.NONE
    assert result_for(results, small).resolution is Resolution.NONE
    assert result_for(results, fire).resolution is Resolution.NONE
    assert small.contract_min == small.contract_max == 5
    assert fire.contract_min == fire.contract_max == 5
    assert a.bankroll == a_initial - 25
    assert b.bankroll == b_initial - 10
    assert_game_invariants(game)


def test_cross_player_ledger_on_win_then_seven_out(game_setup):
    """Reconcile deposits, returned stakes and retained winning principal.

    A Pass Line bet stays up after a point win. B's Don't Pass bet stays up
    after a seven-out win. Neither wager has vig.
    """
    game, a = game_setup
    b = game.add_player()
    a_initial, b_initial = a.bankroll, b.bankroll
    passing = place(game, a, defs.PASS_LINE, 25)
    assert a.bankroll == a_initial - 25
    assert b.bankroll == b_initial
    assert_game_invariants(game)

    for total in (4, 4):
        before = {a: a.bankroll, b: b.bankroll}
        results = roll(game, total)
        assert_roll_accounting(game, before, results)
        assert_game_invariants(game)

    assert passing in game.wagers
    assert game.point is None

    dont = place(game, b, defs.DONT_PASS, 25)
    assert b.bankroll == b_initial - 25
    assert_game_invariants(game)

    # Establish a new point, then seven-out.
    before = {a: a.bankroll, b: b.bankroll}
    results = roll(game, 5)
    assert_roll_accounting(game, before, results)
    assert_game_invariants(game)

    before = {a: a.bankroll, b: b.bankroll}
    results = roll(game, 7)
    assert result_for(results, passing).resolution is Resolution.LOSE
    assert result_for(results, dont).resolution is Resolution.WIN
    assert_roll_accounting(game, before, results)
    assert_game_invariants(game)
    assert passing not in game.wagers
    assert dont in game.wagers
    assert game.point is None
    assert game.shooter_roll_count == 0

    # Pass Line won then lost on the same retained stake; Don't Pass
    # won on its retained stake. No vig in this test.
    assert a.bankroll == a_initial
    assert b.bankroll == b_initial


def test_bonus_tracking_and_contract_invariants_through_rolls(game_setup):
    """Exercise persistent progress and eventual bonus cleanup with invariants."""
    game, player = game_setup
    small = place(game, player, defs.ATS_SMALL, 5)
    tall = place(game, player, defs.ATS_TALL, 5)
    all_bet = place(game, player, defs.ATS_ALL, 5)
    fire = place(game, player, defs.FIRE_BET, 5)

    # No seven: all three ATS sets complete and Fire makes six distinct points.
    for number in (2, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 12):
        results = roll(game, number)
        assert_game_invariants(game)

    assert small not in game.wagers
    assert tall not in game.wagers
    assert all_bet not in game.wagers
    assert fire not in game.wagers
    assert fire.targets_hit == {4, 5, 6, 8, 9, 10}
    assert game.point is None

