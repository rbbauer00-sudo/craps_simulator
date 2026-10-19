
import pytest

from engine import Game, Wager, defs
from simulator import Simulator
from simulator.statistics import SessionStatistics


# ========================
# TEST HELPERS
# ========================

def get_stats(sim: Simulator) -> SessionStatistics:
    return SessionStatistics(
        sim.recorder.rolls,
        opening_players=sim.recorder.opening_players,
        closing_players=sim.recorder.closing_players or (),
    )


def place_wager(
    game: Game,
    player,
    definition,
    value: int,
    target=None,
) -> Wager:
    wager = Wager(
        game=game,
        player=player,
        definition=definition,
        value=value,
        target=target,
    )
    game.place_wager(wager)
    return wager


# ========================
# CLOSING STATE
# ========================

def test_close_captures_player_and_wager_state():
    game = Game(predetermined_rolls=[(2, 2)])
    player = game.add_player()
    sim = Simulator(game)

    wager = place_wager(
        game, player, defs.PASS_LINE, 25
    )

    sim.step()
    sim.close()

    assert sim.recorder.is_closed
    assert sim.recorder.roll_count == 1

    assert len(sim.recorder.closing_players) == 1
    assert len(sim.recorder.closing_wagers) == 1

    assert sim.recorder.closing_wagers[0].wager_id == wager.id
    assert wager in game.wagers

    stats = get_stats(sim)
    player_stats = stats.player(player.id)

    assert player_stats.starting_equity == 1500
    assert player_stats.ending_equity == 1500
    assert player_stats.closing_bankroll == 1475
    assert player_stats.closing_liquid_equity == 1475
    assert player_stats.net_profit == 0


# ========================
# CLOSING AFTER FINAL ADJUSTMENT
# ========================

def test_close_captures_adjustments_after_last_roll():
    game = Game(predetermined_rolls=[(1, 2)])
    player = game.add_player()
    sim = Simulator(game)

    wager = place_wager(
        game, player, defs.PLACE_BET, 24, target=6
    )

    sim.step()

    # $24 -> $36 -> $30, after the last roll.
    game.increase_wager(wager, 12)
    game.decrease_wager(wager, 6)

    assert wager.value == 30

    sim.close()

    # Historical roll state remains unchanged.
    assert sim.recorder.rolls[-1].wagers_after[0].value == 24

    # Closing state reflects the latest wager value.
    assert sim.recorder.closing_wagers[0].value == 30

    stats = get_stats(sim)
    player_stats = stats.player(player.id)

    assert player_stats.closing_bankroll == 1470
    assert player_stats.closing_liquid_equity == 1500
    assert player_stats.ending_equity == 1500
    assert player_stats.net_profit == 0

    # Post-roll history has not been modified.
    assert player_stats.bankroll_history == (1476,)
    assert player_stats.equity_history == (1500,)


# ========================
# CLOSING AFTER A WIN
# ========================

def test_close_after_win_and_take_down():
    game = Game(predetermined_rolls=[(1, 6)])
    player = game.add_player()
    sim = Simulator(game)

    wager = place_wager(
        game, player, defs.PASS_LINE, 25
    )

    sim.step()

    assert player.get_equity().total_equity == 1525

    game.take_down_wager(wager)
    sim.close()

    stats = get_stats(sim)
    player_stats = stats.player(player.id)

    assert sim.recorder.closing_wagers == ()
    assert player_stats.closing_bankroll == 1525
    assert player_stats.closing_liquid_equity == 1525
    assert player_stats.ending_equity == 1525
    assert player_stats.net_profit == 25


# ========================
# NO ROLLS
# ========================

def test_close_without_rolls():
    game = Game()
    player = game.add_player()
    sim = Simulator(game)

    sim.close()
    stats = get_stats(sim)

    assert sim.recorder.is_closed
    assert sim.recorder.closing_wagers == ()
    assert stats.roll_count == 0

    player_stats = stats.player(player.id)

    assert player_stats.starting_equity == 1500
    assert player_stats.ending_equity == 1500
    assert player_stats.closing_bankroll == 1500
    assert player_stats.closing_liquid_equity == 1500
    assert player_stats.net_profit == 0
    assert player_stats.equity_curve == (1500,)


# ========================
# CLOSED SESSION IS FINAL
# ========================

def test_closed_simulator_rejects_new_rolls():
    game = Game(predetermined_rolls=[(1, 2)])
    game.add_player()

    sim = Simulator(game)
    sim.close()

    with pytest.raises(RuntimeError):
        sim.step()

    with pytest.raises(RuntimeError):
        sim.run(1)

    with pytest.raises(RuntimeError):
        sim.close()

    assert sim.recorder.roll_count == 0


# ========================
# CLOSING SNAPSHOT IMMUTABILITY
# ========================

def test_closing_snapshot_does_not_change():
    game = Game()
    player = game.add_player()
    sim = Simulator(game)

    sim.close()

    closing = sim.recorder.closing_players
    assert closing[0].equity.bankroll == 1500

    # The engine can still operate independently.
    player.withdraw(100)

    assert player.bankroll == 1400

    # Recorded snapshots remain unchanged.
    assert closing[0].equity.bankroll == 1500
    assert sim.recorder.closing_players == closing

    stats = get_stats(sim)

    assert stats.player(player.id).ending_equity == 1500
    assert stats.player(player.id).closing_bankroll == 1500


# ========================
# CLOSING EQUITY USED BY STATISTICS
# ========================

def test_closing_equity_used_in_statistics():
    game = Game()
    player = game.add_player()
    sim = Simulator(game)

    sim.close()
    stats = get_stats(sim)

    player_stats = stats.player(player.id)

    assert player_stats.starting_equity == 1500
    assert player_stats.ending_equity == 1500
    assert player_stats.closing_bankroll == 1500
    assert player_stats.closing_liquid_equity == 1500


# ========================
# CLOSING AFTER EXTERNAL BANKROLL CHANGE
# ========================

def test_closing_change_included_in_equity_curve():
    game = Game()
    player = game.add_player()
    sim = Simulator(game)

    # Test that closing values are incorporated even
    # when no rolls occurred.
    player.withdraw(100)

    sim.close()
    stats = get_stats(sim)
    player_stats = stats.player(player.id)

    assert player_stats.starting_equity == 1500
    assert player_stats.ending_equity == 1400
    assert player_stats.equity_curve == (1500, 1400)

    assert player_stats.maximum_drawdown == 100
    assert player_stats.maximum_drawdown_pct == pytest.approx(
        100 / 1500
    )


# ========================
# MULTIPLE PLAYERS
# ========================

def test_close_captures_multiple_players():
    game = Game()
    alice = game.add_player("Alice")
    bob = game.add_player("Bob")

    sim = Simulator(game)

    player_wager = place_wager(
        game, alice, defs.PLACE_BET, 24, target=6
    )

    sim.close()
    stats = get_stats(sim)

    assert set(stats.player_ids) == {alice.id, bob.id}

    assert stats.player(alice.id).closing_bankroll == 1476
    assert stats.player(alice.id).closing_liquid_equity == 1500
    assert stats.player(alice.id).ending_equity == 1500

    assert stats.player(bob.id).closing_bankroll == 1500
    assert stats.player(bob.id).ending_equity == 1500

    assert len(sim.recorder.closing_wagers) == 1
    assert sim.recorder.closing_wagers[0].wager_id == player_wager.id


# ========================
# RECORDER RESET
# ========================

def test_recorder_clear_resets_closing_state():
    game = Game()
    game.add_player()

    sim = Simulator(game)
    sim.close()

    assert sim.recorder.is_closed

    sim.recorder.clear()

    assert not sim.recorder.is_closed
    assert sim.recorder.roll_count == 0
    assert sim.recorder.opening_players == ()
    assert sim.recorder.closing_players is None
    assert sim.recorder.closing_wagers is None

    # A new session can capture a fresh opening.
    sim.recorder.capture_opening(game)

    assert len(sim.recorder.opening_players) == 1
