
import pytest

from engine import Game, Wager, WagerType, Resolution, defs
from simulator import Simulator, WagerStatistics


@pytest.fixture
def wager_stats_setup():
    game = Game(predetermined_rolls=[
        (2, 2),  # Establish point 4
        (1, 3),  # Make point 4: WIN
        (1, 2),  # Come-out 3: LOSE
    ])

    player = game.add_player()

    wager = Wager(
        definition=defs.PASS_LINE,
        player=player,
        game=game,
        value=25,
    )

    game.place_wager(wager)

    sim = Simulator(game)
    sim.run(3)

    stats = WagerStatistics(sim.recorder.rolls)

    return game, player, sim, stats


# ========================
# RESOLUTION COUNTS
# ========================

def test_resolution_counts(wager_stats_setup):
    game, player, sim, stats = wager_stats_setup

    assert stats.wins == 1
    assert stats.losses == 1
    assert stats.pushes == 0
    assert stats.moves == 0

    assert stats.resolution_counts[Resolution.NONE] == 1
    assert stats.win_rate == 0.5


# ========================
# PROFIT AND LOSS
# ========================

def test_wager_profit_and_loss(wager_stats_setup):
    game, player, sim, stats = wager_stats_setup

    assert stats.winning_profit == 25
    assert stats.lost_stakes == 25
    assert stats.net_resolution_result == 0

    # No vig or additional wagers in this example.
    assert player.get_equity().total_equity == 1500


# ========================
# WAGER TYPE FILTERING
# ========================

def test_wager_type_filter(wager_stats_setup):
    game, player, sim, stats = wager_stats_setup

    pass_stats = WagerStatistics(
        sim.recorder.rolls,
        wager_type=WagerType.PASS_LINE,
    )

    field_stats = WagerStatistics(
        sim.recorder.rolls,
        wager_type=WagerType.FIELD,
    )

    assert pass_stats.wins == 1
    assert pass_stats.losses == 1

    assert field_stats.wins == 0
    assert field_stats.losses == 0


# ========================
# PLAYER FILTERING
# ========================

def test_player_filter():
    game = Game(predetermined_rolls=[
        (1, 6),  # Come-out seven
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
    sim.step()

    alice_stats = WagerStatistics(
        sim.recorder.rolls,
        player_id=alice.id,
    )
    bob_stats = WagerStatistics(
        sim.recorder.rolls,
        player_id=bob.id,
    )

    assert alice_stats.wins == 1
    assert alice_stats.winning_profit == 25

    assert bob_stats.wins == 0
    assert bob_stats.winning_profit == 0


# ========================
# EMPTY SESSION
# ========================

def test_empty_wager_statistics():
    stats = WagerStatistics([])

    assert stats.wins == 0
    assert stats.losses == 0
    assert stats.win_rate == 0.0
    assert stats.winning_profit == 0
    assert stats.lost_stakes == 0
    assert stats.net_resolution_result == 0
    assert stats.outcomes_by_type == {}


# ========================
# GROUPING BY TYPE
# ========================

def test_outcomes_by_type(wager_stats_setup):
    game, player, sim, stats = wager_stats_setup

    pass_counts = stats.outcomes_by_type[
        WagerType.PASS_LINE
    ]

    assert pass_counts[Resolution.WIN] == 1
    assert pass_counts[Resolution.LOSE] == 1
    assert pass_counts[Resolution.NONE] == 1



# ========================
# LIFECYCLE
# ========================

def test_persistent_wager_exposure():
    game = Game(predetermined_rolls=[
        (2, 2),  # Establish 4
        (1, 3),  # Win on 4
        (3, 3),  # Establish 6
        (2, 3),  # No resolution
        (1, 6),  # Seven-out
    ])

    player = game.add_player()

    wager = Wager(
        definition=defs.PASS_LINE,
        player=player,
        game=game,
        value=25,
    )
    game.place_wager(wager)

    simulator = Simulator(game)
    simulator.run(5)

    stats = WagerStatistics(
        simulator.recorder.rolls,
        player_id=player.id,
        wager_type=WagerType.PASS_LINE,
    )

    assert stats.wins == 1
    assert stats.losses == 1
    assert stats.winning_profit == 25
    assert stats.lost_stakes == 25
    assert stats.net_resolution_result == 0

    assert stats.resolved_wager_amount == 50
    assert stats.roll_exposure == 125
    assert stats.net_return_on_resolved_amount == 0.0