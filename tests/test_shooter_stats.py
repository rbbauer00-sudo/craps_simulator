
import pytest

from engine import Game
from simulator import Simulator, ShooterStatistics


@pytest.fixture
def shooter_stats_setup():
    game = Game(predetermined_rolls=[
        (2, 2),  # 4: Shooter A establishes point
        (1, 3),  # 4: Shooter A makes point
        (3, 3),  # 6: Shooter A establishes point
        (1, 6),  # 7: Shooter A seven-out
        (2, 3),  # 5: Shooter B establishes point
        (1, 6),  # 7: Shooter B seven-out
    ])

    a = game.add_player("A")
    b = game.add_player("B")

    sim = Simulator(game)
    sim.run(6)

    stats = ShooterStatistics(sim.recorder.rolls)

    return game, a, b, sim, stats


# ========================
# BASIC STATISTICS
# ========================

def test_hand_lengths(shooter_stats_setup):
    game, a, b, sim, stats = shooter_stats_setup

    assert stats.total_rolls == 6
    assert stats.completed_hands == 2
    assert stats.seven_outs == 2
    assert stats.hand_lengths == (4, 2)

    assert stats.average_hand_length == 3.0
    assert stats.longest_hand == 4
    assert stats.shortest_hand == 2
    assert stats.active_hand_length == 0


# ========================
# POINT TRACKING
# ========================

def test_shooter_points(shooter_stats_setup):
    game, a, b, sim, stats = shooter_stats_setup

    assert stats.points_established == 3
    assert stats.points_made == 1
    assert stats.point_make_rate == pytest.approx(1 / 3)


# ========================
# PER-SHOOTER STATISTICS
# ========================

def test_stats_by_shooter(shooter_stats_setup):
    game, a, b, sim, stats = shooter_stats_setup

    assert stats.rolls_by_shooter[a.id] == 4
    assert stats.rolls_by_shooter[b.id] == 2

    assert stats.hands_by_shooter[a.id] == 1
    assert stats.hands_by_shooter[b.id] == 1

    assert stats.points_made_by_shooter[a.id] == 1
    assert stats.points_made_by_shooter[b.id] == 0


# ========================
# INCOMPLETE HAND
# ========================

def test_active_hand_excluded_from_averages():
    game = Game(predetermined_rolls=[
        (2, 2),  # Establish 4
        (1, 3),  # Make 4
        (3, 3),  # Establish 6
    ])

    game.add_player()
    sim = Simulator(game)
    sim.run(3)

    stats = ShooterStatistics(sim.recorder.rolls)

    assert stats.completed_hands == 0
    assert stats.hand_lengths == ()
    assert stats.active_hand_length == 3
    assert stats.average_hand_length == 0.0
    assert stats.longest_hand == 0


# ========================
# EMPTY SESSION
# ========================

def test_empty_session():
    stats = ShooterStatistics([])

    assert stats.total_rolls == 0
    assert stats.completed_hands == 0
    assert stats.hand_lengths == ()
    assert stats.active_hand_length == 0
    assert stats.points_established == 0
    assert stats.points_made == 0
    assert stats.point_make_rate == 0.0
    assert not stats.rolls_by_shooter


# ========================
# COME-OUT SEVEN
# ========================

def test_comeout_seven_does_not_end_hand():
    game = Game(predetermined_rolls=[
        (1, 6),  # Come-out 7
        (2, 2),  # Establish point 4
        (1, 6),  # Seven-out
    ])

    game.add_player()
    sim = Simulator(game)
    sim.run(3)

    stats = ShooterStatistics(sim.recorder.rolls)

    assert stats.total_rolls == 3
    assert stats.seven_outs == 1
    assert stats.hand_lengths == (3,)
