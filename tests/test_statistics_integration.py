
import pytest

from engine import (
    Game,
    Wager,
    WagerType,
    Resolution,
    defs,
)
from simulator import Simulator
from simulator.statistics import (
    SessionStatistics,
    WagerChangeType,
)


def place_wager(game, player, definition, value, target=None):
    wager = Wager(
        game=game,
        player=player,
        definition=definition,
        value=value,
        target=target,
    )
    game.place_wager(wager)
    return wager


def assert_player_accounting(stats, player_id):
    player_stats = stats.player(player_id)
    wager_stats = stats.wager_stats(player_id=player_id)

    assert (
        player_stats.net_profit
        == wager_stats.net_resolution_result
    )


# ========================
# WIN AND LOSS ACCOUNTING
# ========================

def test_pass_line_accounting():
    game = Game(predetermined_rolls=[
        (2, 2),  # Establish 4
        (1, 3),  # Make 4, WIN
        (3, 3),  # Establish 6
        (1, 6),  # Seven-out, LOSE
    ])

    player = game.add_player()

    place_wager(
        game, player, defs.PASS_LINE, 25
    )

    sim = Simulator(game)
    sim.run(4)

    stats = SessionStatistics(sim.recorder.rolls)

    assert stats.player(player.id).net_profit == 0
    assert stats.wagers.winning_profit == 25
    assert stats.wagers.lost_stakes == 25

    assert_player_accounting(stats, player.id)


# ========================
# PERSISTENT WAGER ACCOUNTING
# ========================

def test_persistent_wager_accounting():
    game = Game(predetermined_rolls=[
        (2, 2),
        (1, 3),
        (3, 3),
        (1, 6),
    ])

    player = game.add_player()
    wager = place_wager(
        game, player, defs.PASS_LINE, 25
    )

    sim = Simulator(game)
    sim.run(4)

    records = sim.recorder.rolls
    outcomes = [
        outcome
        for record in records
        for outcome in record.wager_outcomes
        if outcome.wager_id == wager.id
    ]

    assert sum(
        outcome.resolution is Resolution.WIN
        for outcome in outcomes
    ) == 1

    assert sum(
        outcome.resolution is Resolution.LOSE
        for outcome in outcomes
    ) == 1

    # Winning does not generate a new wager.
    assert all(
        not record.wager_changes_before
        for record in records[1:]
    )

    stats = SessionStatistics(records)
    assert_player_accounting(stats, player.id)


# ========================
# MULTIPLE PLAYERS
# ========================

def test_independent_player_accounting():
    game = Game(predetermined_rolls=[
        (2, 2),
        (1, 3),
    ])

    alice = game.add_player("Alice")
    bob = game.add_player("Bob")

    place_wager(game, alice, defs.PASS_LINE, 25)
    place_wager(game, bob, defs.PASS_LINE, 50)

    sim = Simulator(game)
    sim.run(2)

    stats = SessionStatistics(sim.recorder.rolls)

    assert stats.player(alice.id).net_profit == 25
    assert stats.player(bob.id).net_profit == 50

    assert_player_accounting(stats, alice.id)
    assert_player_accounting(stats, bob.id)


# ========================
# NET COMMITTED ADJUSTMENTS
# ========================

def test_adjustments_do_not_create_profit():
    game = Game(predetermined_rolls=[
        (2, 3),  # Establish point 5
        (2, 3),  # Make point 5
    ])

    player = game.add_player()
    wager = place_wager(
        game, player, defs.PLACE_BET, 24, target=6
    )

    sim = Simulator(game)
    sim.step()

    # $24 -> $36 -> $30
    game.increase_wager(wager, 12)
    game.decrease_wager(wager, 6)

    sim.step()

    records = sim.recorder.rolls
    changes = records[1].wager_changes_before

    assert len(changes) == 1
    assert changes[0].change_type is WagerChangeType.ADJUST
    assert changes[0].value_change == 6

    stats = SessionStatistics(records)

    # No winning or losing resolution on the Place 6.
    assert stats.player(player.id).net_profit == 0
    assert stats.wagers.net_resolution_result == 0

    assert_player_accounting(stats, player.id)


def test_equity_matches_outcomes_on_each_roll():
    game = Game(predetermined_rolls=[
        (2, 2),
        (1, 3),
        (3, 3),
        (1, 6),
    ])

    player = game.add_player()
    place_wager(game, player, defs.PASS_LINE, 25)

    sim = Simulator(game)
    sim.run(4)

    for record in sim.recorder.rolls:
        before = next(
            p.equity.total_equity
            for p in record.players_before
            if p.player_id == player.id
        )
        after = next(
            p.equity.total_equity
            for p in record.players_after
            if p.player_id == player.id
        )

        wagers = {
            w.wager_id: w
            for w in record.wagers_before
        }

        resolution_profit = 0

        for outcome in record.wager_outcomes:
            wager = wagers[outcome.wager_id]

            if wager.player_id != player.id:
                continue

            if outcome.resolution is Resolution.WIN:
                resolution_profit += outcome.profit

            elif outcome.resolution is Resolution.LOSE:
                resolution_profit -= wager.value

        assert after - before == resolution_profit