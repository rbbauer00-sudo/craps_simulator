"""Player accounting and ownership tests.

Assumes the Player.get_equity() / PlayerEquity API discussed for engine v1.0
has been implemented. The tests below intentionally do not duplicate wager
resolution rules already covered in the wager-specific suites.
"""

import pytest

from engine import Game, Wager, defs
from engine.exceptions import InsufficientFundsError


STARTING_BANKROLL = 1500
BET_AMOUNT = 25


# =======================
# INITIALIZATION
# =======================


def test_player_defaults(game_setup):
    game, player = game_setup

    assert player.game is game
    assert player in game.players
    assert player.name == "Player 0"
    assert player.id == 0
    assert player.bankroll == STARTING_BANKROLL
    assert player.get_wagers() == []


def test_player_custom_initialization():
    game = Game()
    player = game.add_player(name="Alice", bankroll=500)

    assert player.name == "Alice"
    assert player.bankroll == 500
    assert player.id == 0
    assert str(player) == "Alice"
    assert repr(player) == "Player Obj: Alice"


# =======================
# DEPOSITS / WITHDRAWALS
# =======================


@pytest.mark.parametrize("amount", [1, 25, 1500])
def test_deposit(game_setup, amount):
    _, player = game_setup

    assert player.deposit(amount) is None
    assert player.bankroll == STARTING_BANKROLL + amount


@pytest.mark.parametrize("amount", [1, 25, 1500])
def test_withdraw(game_setup, amount):
    _, player = game_setup

    assert player.withdraw(amount) is None
    assert player.bankroll == STARTING_BANKROLL - amount


@pytest.mark.parametrize("operation", ["deposit", "withdraw"])
def test_negative_transaction_rejected_without_mutation(game_setup, operation):
    _, player = game_setup

    with pytest.raises(ValueError):
        getattr(player, operation)(-1)

    assert player.bankroll == STARTING_BANKROLL


def test_insufficient_funds_rejected_without_mutation(game_setup):
    _, player = game_setup

    with pytest.raises(InsufficientFundsError):
        player.withdraw(STARTING_BANKROLL + 1)

    assert player.bankroll == STARTING_BANKROLL


def test_withdraw_exact_balance(game_setup):
    _, player = game_setup

    player.withdraw(STARTING_BANKROLL)

    assert player.bankroll == 0


def test_set_bankroll(game_setup):
    _, player = game_setup

    player.set_bankroll(250)
    assert player.bankroll == 250

    player.set_bankroll(0)
    assert player.bankroll == 0


@pytest.mark.parametrize("invalid", [-1, 1.5, "500", True, None])
def test_set_bankroll_rejects_invalid_values(game_setup, invalid):
    _, player = game_setup

    with pytest.raises(ValueError):
        player.set_bankroll(invalid)

    assert player.bankroll == STARTING_BANKROLL


# =======================
# WAGER INVENTORY
# =======================


def test_player_get_wagers_tracks_active_wagers(game_setup):
    game, player = game_setup
    wager = Wager(
        definition=defs.PASS_LINE, 
        player=player, 
        game=game,
        value=BET_AMOUNT,
    )

    assert player.get_wagers() == []

    game.place_wager(wager)
    assert player.get_wagers() == [wager]
    assert player.funds_on_table == BET_AMOUNT

    game.take_down_wager(wager)
    assert player.get_wagers() == []
    assert player.funds_on_table == 0
    assert player.bankroll == STARTING_BANKROLL


def test_player_wagers_are_isolated():
    game = Game()
    alice = game.add_player(name="Alice")
    bob = game.add_player(name="Bob")

    alice_wager = Wager(
        definition=defs.PASS_LINE, 
        game=game,
        player=alice, 
        value=25,
    )
    bob_wager = Wager(
        definition=defs.PASS_LINE, 
        player=bob, 
        game=game,
        value=50,
    )

    game.place_wager(alice_wager)
    game.place_wager(bob_wager)

    assert alice.get_wagers() == [alice_wager]
    assert bob.get_wagers() == [bob_wager]
    assert alice.funds_on_table == 25
    assert bob.funds_on_table == 50
    assert alice.bankroll == 1475
    assert bob.bankroll == 1450


# =======================
# FUNDS AND EQUITY
# =======================


def assert_equity(player, *, bankroll, removable, reserved, total):
    """Assert the snapshot fields and their accounting invariants."""
    equity = player.get_equity()

    assert equity.bankroll == bankroll
    assert equity.removable_equity == removable
    assert equity.reserved_equity == reserved
    assert equity.liquid_equity == bankroll + removable
    assert equity.total_equity == total

    assert equity.total_equity == (
        equity.liquid_equity + equity.reserved_equity
    )
    assert equity.total_equity == bankroll + player.funds_on_table


def test_player_equity_with_no_wagers(game_setup):
    _, player = game_setup

    assert player.funds_on_table == 0
    assert player.contracted_funds == 0
    assert player.removable_funds == 0
    assert_equity(
        player, bankroll=1500, removable=0, reserved=0, total=1500
    )


def test_player_equity_on_comeout(game_setup):
    game, player = game_setup
    game.place_wager(
        Wager(definition=defs.PASS_LINE, 
              game=game,
              player=player, 
              value=25,
        )
    )

    assert player.contracted_funds == 0
    assert player.removable_funds == 25
    assert_equity(
        player, bankroll=1475, removable=25, reserved=0, total=1500
    )


def test_player_equity_after_point_established(game_setup):
    game, player = game_setup
    game.place_wager(
        Wager(
            definition=defs.PASS_LINE, 
            player=player, 
            game=game,
            value=25,
        )
    )

    result = game.roll(2, 2)  # Establish point 4; Pass Line contracted
    assert result.point_after == 4

    assert player.contracted_funds == 25
    assert player.removable_funds == 0
    assert_equity(
        player, bankroll=1475, removable=0, reserved=25, total=1500
    )


def test_player_equity_after_pass_line_loss(game_setup):
    game, player = game_setup
    game.place_wager(
        Wager(
            definition=defs.PASS_LINE, 
            player=player, 
            game=game,
            value=25,
        )
    )

    result = game.roll(1, 2)  # Come-out 3: immediate loss
    assert result.roll.total == 3
    assert player.get_wagers() == []
    assert_equity(
        player, bankroll=1475, removable=0, reserved=0, total=1475
    )


def test_equity_snapshot_does_not_change_after_future_rolls(game_setup):
    game, player = game_setup
    game.place_wager(
        Wager(
            definition=defs.PASS_LINE, 
            player=player, 
            game=game,
            value=25,
        )
    )

    before = player.get_equity()
    game.roll(1, 2)  # Loss
    after = player.get_equity()

    assert before.total_equity == 1500
    assert after.total_equity == 1475
    assert before.total_equity == 1500  # Snapshot has not mutated


# =======================
# MULTIPLE PLAYER ISOLATION
# =======================


def test_player_transactions_are_independent():
    game = Game()
    alice = game.add_player(name="Alice", bankroll=500)
    bob = game.add_player(name="Bob", bankroll=1000)

    alice.withdraw(100)
    bob.deposit(75)

    assert alice.bankroll == 400
    assert bob.bankroll == 1075
    assert alice.id == 0
    assert bob.id == 1
