
import pytest

from engine import Game, Wager, WagerType, defs
from simulator import Simulator
from simulator.statistics import (
    SessionStatistics,
    DiceStatistics,
    ShooterStatistics,
    PlayerStatistics,
    WagerStatistics,
)


@pytest.fixture
def session_stats_setup():
    game = Game(predetermined_rolls=[
        (2, 2),  # Establish point 4
        (1, 3),  # Make point 4
        (3, 3),  # Establish point 6
        (1, 6),  # Seven-out
    ])

    alice = game.add_player("Alice")
    bob = game.add_player("Bob")

    wager = Wager(
        definition=defs.PASS_LINE,
        player=alice,
        game=game,
        value=25,
    )
    game.place_wager(wager)

    sim = Simulator(game)
    sim.run(4)

    stats = SessionStatistics(sim.recorder.rolls)

    return game, alice, bob, sim, stats


def test_session_analyzers(session_stats_setup):
    game, alice, bob, sim, stats = session_stats_setup

    assert stats.roll_count == 4
    assert isinstance(stats.dice, DiceStatistics)
    assert isinstance(stats.shooters, ShooterStatistics)
    assert isinstance(stats.wagers, WagerStatistics)

    assert stats.dice.total_rolls == 4
    assert stats.shooters.completed_hands == 1
    assert stats.shooters.hand_lengths == (4,)

    assert stats.wagers.wins == 1
    assert stats.wagers.losses == 1


def test_player_discovery(session_stats_setup):
    game, alice, bob, sim, stats = session_stats_setup

    assert stats.player_ids == tuple(sorted((
        alice.id,
        bob.id,
    )))

    assert isinstance(
        stats.player(alice.id),
        PlayerStatistics,
    )

    assert stats.player(alice.id).net_profit == 0
    assert stats.player(bob.id).net_profit == 0

    with pytest.raises(KeyError):
        stats.player(999999)


def test_filtered_wager_statistics(session_stats_setup):
    game, alice, bob, sim, stats = session_stats_setup

    alice_pass = stats.wager_stats(
        player_id=alice.id,
        wager_type=WagerType.PASS_LINE,
    )

    bob_pass = stats.wager_stats(
        player_id=bob.id,
        wager_type=WagerType.PASS_LINE,
    )

    assert alice_pass.wins == 1
    assert alice_pass.losses == 1

    assert bob_pass.wins == 0
    assert bob_pass.losses == 0

    assert stats.wager_stats() is stats.wagers


def test_analyzers_are_cached(session_stats_setup):
    game, alice, bob, sim, stats = session_stats_setup

    assert stats.dice is stats.dice
    assert stats.shooters is stats.shooters
    assert stats.wagers is stats.wagers

    assert (
        stats.player(alice.id)
        is stats.player(alice.id)
    )


def test_snapshot_does_not_change():
    game = Game(predetermined_rolls=[
        (2, 2),
        (1, 3),
    ])
    game.add_player()

    sim = Simulator(game)

    sim.step()
    first_stats = SessionStatistics(sim.recorder.rolls)

    sim.step()
    updated_stats = SessionStatistics(sim.recorder.rolls)

    assert first_stats.roll_count == 1
    assert first_stats.dice.total_rolls == 1

    assert updated_stats.roll_count == 2
    assert updated_stats.dice.total_rolls == 2


def test_empty_session():
    stats = SessionStatistics(())

    assert stats.roll_count == 0
    assert stats.player_ids == ()
    assert stats.players == {}

    assert stats.dice.total_rolls == 0
    assert stats.shooters.completed_hands == 0
    assert stats.wagers.wins == 0
