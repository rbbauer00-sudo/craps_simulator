
import pytest

from engine import Game, Wager, defs
from engine.game import GameSettings
from engine.enums import VigSetting
from simulator import Simulator
from simulator.statistics import SessionStatistics


def get_stats(sim):
    return SessionStatistics(
        sim.recorder.rolls,
        opening_players=sim.recorder.opening_players,
    )


# ========================
# OPENING STATE
# ========================

def test_opening_equity_captured_before_first_roll():
    game = Game(predetermined_rolls=[(2, 2)])
    player = game.add_player()

    sim = Simulator(game)

    assert len(sim.recorder.opening_players) == 1
    assert (
        sim.recorder.opening_players[0].equity.total_equity
        == 1500
    )

    wager = Wager(
        game=game,
        player=player,
        definition=defs.PASS_LINE,
        value=25,
    )
    game.place_wager(wager)

    sim.step()
    stats = get_stats(sim)

    assert stats.player(player.id).starting_equity == 1500
    assert stats.player(player.id).ending_equity == 1500
    assert stats.player(player.id).net_profit == 0


# ========================
# UPFRONT VIG AT SESSION START
# ========================

def test_upfront_buy_preserves_opening_baseline():
    game = Game(
        settings=GameSettings(
            buy_vig_setting=VigSetting.UP_FRONT,
        ),
        predetermined_rolls=[(1, 2)],
    )
    player = game.add_player()

    sim = Simulator(game)

    wager = Wager(
        game=game,
        player=player,
        definition=defs.PLACE_BET,
        value=100,
        target=4,
        _is_buy=True,
    )
    game.place_wager(wager)

    assert wager.collected_vig == 5

    sim.step()
    stats = get_stats(sim)
    player_stats = stats.player(player.id)

    assert player_stats.starting_equity == 1500

    assert (
        player_stats.ending_equity
        == player.get_equity().total_equity
    )

    assert (
        player_stats.net_profit
        == player.get_equity().total_equity - 1500
    )

    # Verify the first roll snapshot does not replace
    # the true session-opening financial baseline.
    assert (
        sim.recorder.opening_players[0].equity.total_equity
        == 1500
    )


# ========================
# NO ROLLS
# ========================

def test_session_with_no_rolls():
    game = Game()
    player = game.add_player()

    sim = Simulator(game)
    stats = get_stats(sim)

    assert stats.roll_count == 0
    assert stats.player_ids == (player.id,)

    player_stats = stats.player(player.id)

    assert player_stats.roll_count == 0
    assert player_stats.starting_equity == 1500
    assert player_stats.ending_equity == 1500
    assert player_stats.net_profit == 0
    assert player_stats.equity_curve == (1500,)


# ========================
# PLAYER JOINS MID-SESSION
# ========================

def test_player_joins_after_session_opens():
    game = Game(predetermined_rolls=[
        (2, 2),
        (1, 3),
    ])

    alice = game.add_player("Alice")
    sim = Simulator(game)

    sim.step()

    bob = game.add_player("Bob")
    sim.step()

    stats = get_stats(sim)

    assert alice.id in stats.player_ids
    assert bob.id in stats.player_ids

    assert stats.player(alice.id).starting_equity == 1500
    assert stats.player(bob.id).starting_equity == 1500

    assert stats.player(bob.id).roll_count == 1
    assert stats.player(bob.id).net_profit == 0


# ========================
# UNRESOLVED WAGER
# ========================

def test_session_ends_with_unresolved_wager():
    game = Game(predetermined_rolls=[
        (2, 2),  # Point 4 established
    ])
    player = game.add_player()
    sim = Simulator(game)

    wager = Wager(
        game=game,
        player=player,
        definition=defs.PASS_LINE,
        value=25,
    )
    game.place_wager(wager)

    sim.step()
    stats = get_stats(sim)
    player_stats = stats.player(player.id)

    assert wager in game.wagers
    assert player.bankroll == 1475

    # Bankroll is reduced, but wager principal is
    # still included in total equity.
    assert player_stats.ending_equity == 1500
    assert player_stats.net_profit == 0

    assert player_stats.bankroll_history == (1475,)


# ========================
# SNAPSHOT IMMUTABILITY
# ========================

def test_opening_snapshot_does_not_change():
    game = Game(predetermined_rolls=[(1, 6)])
    player = game.add_player()
    sim = Simulator(game)

    opening = sim.recorder.opening_players

    wager = Wager(
        game=game,
        player=player,
        definition=defs.PASS_LINE,
        value=25,
    )
    game.place_wager(wager)

    sim.step()

    assert opening == sim.recorder.opening_players
    assert opening[0].equity.total_equity == 1500
    assert player.get_equity().total_equity == 1525
