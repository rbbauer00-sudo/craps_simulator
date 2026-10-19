
import pytest

from engine import Game, Wager, GameSettings, defs
from engine.enums import VigSetting
from simulator import Simulator
from simulator.statistics import (
    SessionStatistics,
    SessionFinancialSummary,
)


def get_stats(sim):
    return SessionStatistics(
        sim.recorder.rolls,
        opening_players=sim.recorder.opening_players,
        closing_players=sim.recorder.closing_players or (),
        closing_wagers=sim.recorder.closing_wagers or (),
    )


def place_wager(
    game, player, definition, value, target=None,
    **kwargs,
):
    wager = Wager(
        game=game,
        player=player,
        definition=definition,
        value=value,
        target=target,
        **kwargs,
    )
    game.place_wager(wager)
    return wager


# ========================
# WINNING SESSION
# ========================

def test_financial_summary_after_win():
    game = Game(predetermined_rolls=[
        (1, 6),  # Come-out 7: Pass Line wins
    ])
    player = game.add_player()
    sim = Simulator(game)

    wager = place_wager(
        game, player, defs.PASS_LINE, 25
    )

    sim.step()
    game.take_down_wager(wager)
    sim.close()

    summary = get_stats(sim).financial_summary(player.id)

    assert isinstance(summary, SessionFinancialSummary)

    assert summary.player_id == player.id
    assert summary.roll_count == 1

    assert summary.opening_bankroll == 1500
    assert summary.closing_bankroll == 1525

    assert summary.opening_equity == 1500
    assert summary.closing_equity == 1525
    assert summary.net_equity_change == 25

    assert summary.closing_liquid_equity == 1525
    assert summary.closing_reserved_equity == 0
    assert summary.outstanding_wager_value == 0

    assert summary.wins == 1
    assert summary.losses == 0
    assert summary.winning_profit == 25
    assert summary.lost_stakes == 0
    assert summary.net_resolution_result == 25


# ========================
# OUTSTANDING CONTRACT WAGER
# ========================

def test_financial_summary_with_outstanding_wager():
    game = Game(predetermined_rolls=[
        (2, 2),  # Establish point 4
    ])
    player = game.add_player()
    sim = Simulator(game)

    place_wager(
        game, player, defs.PASS_LINE, 25
    )

    sim.step()
    sim.close()

    summary = get_stats(sim).financial_summary(player.id)

    assert summary.opening_equity == 1500
    assert summary.closing_equity == 1500
    assert summary.net_equity_change == 0

    assert summary.closing_bankroll == 1475
    assert summary.closing_liquid_equity == 1475
    assert summary.closing_reserved_equity == 25
    assert summary.outstanding_wager_value == 25

    assert summary.wins == 0
    assert summary.losses == 0
    assert summary.net_resolution_result == 0


# ========================
# UPFRONT BUY VIG
# ========================

def test_financial_summary_upfront_buy_vig():
    game = Game(
        settings=GameSettings(
            buy_vig_setting=VigSetting.UP_FRONT,
        ),
        predetermined_rolls=[
            (1, 2),  # Buy 4 does not resolve
        ],
    )

    player = game.add_player()
    sim = Simulator(game)

    wager = place_wager(
        game,
        player,
        defs.PLACE_BET,
        100,
        target=4,
        _is_buy=True,
    )

    assert wager.collected_vig == 5

    sim.step()
    sim.close()

    summary = get_stats(sim).financial_summary(player.id)

    assert summary.opening_equity == 1500

    # Engine total equity excludes the $5 held as vig.
    assert summary.closing_equity == 1495
    assert summary.net_equity_change == -5

    assert summary.closing_bankroll == 1395
    assert summary.outstanding_wager_value == 100

    # No wager has won or lost.
    assert summary.wins == 0
    assert summary.losses == 0
    assert summary.net_resolution_result == 0


# ========================
# MULTIPLE PLAYERS
# ========================

def test_financial_summaries_independent():
    game = Game(predetermined_rolls=[
        (1, 6),
    ])

    alice = game.add_player("Alice")
    bob = game.add_player("Bob")

    sim = Simulator(game)

    place_wager(game, alice, defs.PASS_LINE, 25)

    sim.step()
    sim.close()

    stats = get_stats(sim)

    alice_summary = stats.financial_summary(alice.id)
    bob_summary = stats.financial_summary(bob.id)

    assert alice_summary.net_equity_change == 25
    assert bob_summary.net_equity_change == 0

    assert alice_summary.wins == 1
    assert bob_summary.wins == 0

    assert alice_summary.outstanding_wager_value == 25
    assert bob_summary.outstanding_wager_value == 0


# ========================
# NO ROLLS
# ========================

def test_financial_summary_without_rolls():
    game = Game()
    player = game.add_player()
    sim = Simulator(game)

    sim.close()

    summary = get_stats(sim).financial_summary(player.id)

    assert summary.roll_count == 0
    assert summary.opening_bankroll == 1500
    assert summary.closing_bankroll == 1500
    assert summary.net_equity_change == 0
    assert summary.outstanding_wager_value == 0
    assert summary.maximum_drawdown == 0


# ========================
# INCOMPLETE SESSION
# ========================

def test_financial_summary_requires_closing_snapshot():
    game = Game()
    player = game.add_player()
    sim = Simulator(game)

    stats = get_stats(sim)

    with pytest.raises(ValueError):
        stats.financial_summary(player.id)


# ========================
# PLAYER JOINS AFTER OPENING
# ========================

def test_financial_summary_requires_player_opening():
    game = Game()
    game.add_player("Alice")

    sim = Simulator(game)

    bob = game.add_player("Bob")
    sim.close()

    stats = get_stats(sim)

    with pytest.raises(ValueError):
        stats.financial_summary(bob.id)
