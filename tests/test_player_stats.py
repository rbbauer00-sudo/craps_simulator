
import pytest

from engine import Game, Wager, defs
from simulator import Simulator, PlayerStatistics


@pytest.fixture
def player_stats_setup():
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

    simulator = Simulator(game)
    simulator.run(3)

    stats = PlayerStatistics(
        simulator.recorder.rolls,
        player.id,
    )

    return game, player, simulator, stats


# ========================
# EQUITY HISTORY
# ========================

def test_player_equity_history(player_stats_setup):
    game, player, simulator, stats = player_stats_setup

    assert stats.roll_count == 3
    assert stats.starting_equity == 1500

    # Starting equity: 1500
    # Establish point: 1500
    # Win $25: 1525
    # Lose $25 wager: 1500

    assert stats.equity_history == (
        1500, 1525, 1500
    )
    assert stats.equity_curve == (
        1500, 1500, 1525, 1500
    )

    assert stats.ending_equity == 1500
    assert stats.net_profit == 0


# ========================
# BANKROLL HISTORY
# ========================

def test_bankroll_history(player_stats_setup):
    game, player, simulator, stats = player_stats_setup

    assert stats.bankroll_history == (
        1475, 1500, 1500
    )

    assert stats.liquid_equity_history == (
        1475, 1525, 1500
    )


# ========================
# MAXIMUM DRAWDOWN
# ========================

def test_maximum_drawdown(player_stats_setup):
    game, player, simulator, stats = player_stats_setup

    assert stats.peak_equity == 1525
    assert stats.maximum_drawdown == 25
    assert stats.maximum_drawdown_pct == pytest.approx(
        25 / 1525
    )


# ========================
# MULTIPLE PLAYERS
# ========================

def test_player_statistics_are_independent():
    game = Game(predetermined_rolls=[
        (2, 2),
        (1, 3),
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

    simulator = Simulator(game)
    simulator.run(2)

    alice_stats = PlayerStatistics(
        simulator.recorder.rolls, alice.id
    )
    bob_stats = PlayerStatistics(
        simulator.recorder.rolls, bob.id
    )

    assert alice_stats.net_profit == 25
    assert bob_stats.net_profit == 0

    assert alice_stats.ending_equity == 1525
    assert bob_stats.ending_equity == 1500


# ========================
# EMPTY SESSION
# ========================

def test_empty_player_statistics():
    stats = PlayerStatistics([], player_id=0)

    assert stats.roll_count == 0
    assert stats.equity_history == ()
    assert stats.equity_curve == ()
    assert stats.starting_equity == 0
    assert stats.ending_equity == 0
    assert stats.net_profit == 0
    assert stats.maximum_drawdown == 0
    assert stats.maximum_drawdown_pct == 0.0
