
import pytest

from engine import Game, Wager, defs, Resolution
from simulator import Simulator, WagerChangeType


@pytest.fixture
def recorder_game():
    game = Game(predetermined_rolls=[
        (2, 2),  # Establish point 4
        (1, 3),  # Make point 4
        (3, 3),  # Establish point 6
        (1, 6),  # Seven-out
    ])

    player = game.add_player()
    simulator = Simulator(game)

    return simulator, game, player


# ========================
# INITIALIZATION
# ========================

def test_recorder_initialization(recorder_game):
    simulator, game, player = recorder_game

    assert simulator.recorder.roll_count == 0
    assert simulator.recorder.rolls == ()


# ========================
# ROLL RECORDING
# ========================

def test_recorder_tracks_rolls(recorder_game):
    simulator, game, player = recorder_game

    simulator.run(4)

    records = simulator.recorder.rolls

    assert len(records) == 4
    assert simulator.recorder.roll_count == 4
    assert simulator.roll_count == 4

    assert [
        sum(record.dice)
        for record in records
    ] == [4, 4, 6, 7]

    assert [
        record.roll_number
        for record in records
    ] == [1, 2, 3, 4]


# ========================
# SHOOTER INFORMATION
# ========================

def test_recorder_tracks_shooter(recorder_game):
    simulator, game, player = recorder_game

    next_player = game.add_player("Next Shooter")

    simulator.run(4)

    records = simulator.recorder.rolls

    assert [
        record.shooter_roll_count
        for record in records
    ] == [1, 2, 3, 4]

    assert all(
        record.shooter_id == player.id
        for record in records
    )

    assert records[3].seven_out is True
    assert game.shooter_roll_count == 0
    assert game.shooter is next_player


# ========================
# WAGER RESOLUTION
# ========================

def test_recorder_tracks_pass_line_loss():
    game = Game(predetermined_rolls=[
        (2, 2),  # Establish 4
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
    simulator.run(2)

    record = simulator.recorder.rolls[1]

    assert len(record.wagers_before) == 1
    assert len(record.wagers_after) == 0

    outcome = record.wager_outcomes[0]

    assert outcome.wager_id == wager.id
    assert outcome.player_id == player.id
    assert outcome.resolution is Resolution.LOSE
    assert outcome.profit == 0


# ========================
# HISTORICAL IMMUTABILITY
# ========================

def test_recorder_preserves_historical_equity(recorder_game):
    simulator, game, player = recorder_game

    simulator.step()

    original = simulator.recorder.rolls[0]
    original_bankroll = original.players_after[0].equity.bankroll

    player.withdraw(100)

    assert player.bankroll == original_bankroll - 100

    assert (
        simulator.recorder.rolls[0]
        .players_after[0]
        .equity.bankroll
    ) == original_bankroll



def test_recorder_tracks_come_bet_movement():
    game = Game(predetermined_rolls=[
        (3, 3),  # Establish point 6
        (2, 3),  # Come bet travels to 5
    ])
    player = game.add_player()
    simulator = Simulator(game)

    simulator.step()

    wager = Wager(
        definition=defs.COME,
        player=player,
        game=game,
        value=25,
    )
    game.place_wager(wager)

    simulator.step()

    record = simulator.recorder.rolls[1]

    before = record.wagers_before[0]
    after = record.wagers_after[0]
    outcome = record.wager_outcomes[0]

    assert before.wager_id == after.wager_id == wager.id
    assert before.target is None
    assert after.target == 5

    assert outcome.wager_id == wager.id
    assert outcome.resolution is Resolution.MOVE
    assert outcome.move_to == 5


def test_recorder_preserves_wager_history():
    game = Game(predetermined_rolls=[(2, 2)])

    player = game.add_player()

    wager = Wager(
        definition=defs.PLACE_BET,
        player=player,
        game=game,
        value=25,
        target=9
    )
    game.place_wager(wager)

    simulator = Simulator(game)
    simulator.step()

    original = simulator.recorder.rolls[0]

    # Change the live wager after recording.
    game.increase_wager(wager, 25)

    assert wager.value == 50
    assert original.wagers_before[0].value == 25
    assert original.wagers_after[0].value == 25


def test_recorder_tracks_multiple_players():
    game = Game(predetermined_rolls=[(2, 2)])

    player1 = game.add_player("Alice")
    player2 = game.add_player("Bob")

    wager = Wager(
        definition=defs.PASS_LINE,
        player=player2,
        game=game,
        value=25,
    )
    game.place_wager(wager)

    simulator = Simulator(game)
    simulator.step()

    record = simulator.recorder.rolls[0]

    assert len(record.players_before) == 2
    assert len(record.players_after) == 2

    alice, bob = record.players_after

    assert alice.player_id == player1.id
    assert bob.player_id == player2.id

    assert alice.position == 0
    assert bob.position == 1

    assert alice.equity.bankroll == 1500
    assert bob.equity.bankroll == 1475
    assert bob.equity.reserved_equity == 25



# ========================
# COMMITTED WAGER CHANGES
# ========================

def test_initial_wager_placement_recorded():
    game = Game(predetermined_rolls=[(1, 2)])
    player = game.add_player()

    wager = Wager(
        definition=defs.PLACE_BET,
        player=player,
        game=game,
        value=24,
        target=6,
    )
    game.place_wager(wager)

    sim = Simulator(game)
    sim.step()

    changes = sim.recorder.rolls[0].wager_changes_before

    assert len(changes) == 1
    assert changes[0].change_type is WagerChangeType.PLACE
    assert changes[0].wager_id == wager.id
    assert changes[0].value_change == 24


def test_multiple_adjustments_record_as_one_net_change():
    game = Game(predetermined_rolls=[
        (1, 2), (1, 2),
    ])
    player = game.add_player()

    wager = Wager(
        definition=defs.PLACE_BET,
        player=player,
        game=game,
        value=24,
        target=6,
    )
    game.place_wager(wager)

    sim = Simulator(game)
    sim.step()

    # Intermediate adjustments are not committed.
    game.increase_wager(wager, 12)
    game.decrease_wager(wager, 6)

    assert wager.value == 30

    sim.step()

    changes = sim.recorder.rolls[1].wager_changes_before

    assert len(changes) == 1
    assert changes[0].change_type is WagerChangeType.ADJUST
    assert changes[0].before.value == 24
    assert changes[0].after.value == 30
    assert changes[0].value_change == 6


def test_wager_removal_recorded():
    game = Game(predetermined_rolls=[
        (1, 2), (1, 2),
    ])
    player = game.add_player()

    wager = Wager(
        definition=defs.PLACE_BET,
        player=player,
        game=game,
        value=24,
        target=6,
    )
    game.place_wager(wager)

    sim = Simulator(game)
    sim.step()

    game.take_down_wager(wager)
    sim.step()

    changes = sim.recorder.rolls[1].wager_changes_before

    assert len(changes) == 1
    assert changes[0].change_type is WagerChangeType.REMOVE
    assert changes[0].value_change == -24
    assert changes[0].after is None


def test_unmodified_wager_produces_no_change():
    game = Game(predetermined_rolls=[
        (1, 2), (1, 2),
    ])
    player = game.add_player()

    wager = Wager(
        definition=defs.PLACE_BET,
        player=player,
        game=game,
        value=24,
        target=6,
    )
    game.place_wager(wager)

    sim = Simulator(game)
    sim.run(2)

    assert len(sim.recorder.rolls[0].wager_changes_before) == 1
    assert sim.recorder.rolls[1].wager_changes_before == ()



# ========================
# PERSISTENT WAGER LIFECYCLE
# ========================

def test_persistent_wager_multiple_wins_same_id():
    game = Game(predetermined_rolls=[
        (3, 3),  # Place 6 wins
        (3, 3),  # Place 6 wins again
        (1, 2),  # No resolution
        (1, 6),  # Seven-out: Place 6 loses
    ])

    player = game.add_player()

    wager = Wager(
        definition=defs.PLACE_BET,
        player=player,
        game=game,
        value=30,
        target=6,
    )
    game.place_wager(wager)

    original_id = wager.id

    sim = Simulator(game)
    sim.run(4)

    records = sim.recorder.rolls

    # Initial placement occurs only once
    assert len(records[0].wager_changes_before) == 1
    assert (
        records[0].wager_changes_before[0].change_type
        is WagerChangeType.PLACE
    )

    # No changes committed on subsequent rolls
    for record in records[1:]:
        assert record.wager_changes_before == ()

    # Same wager persists through both wins
    assert records[0].wagers_after[0].wager_id == original_id
    assert records[1].wagers_after[0].wager_id == original_id
    assert records[2].wagers_after[0].wager_id == original_id

    # Verify each resolution
    assert [
        record.wager_outcomes[0].resolution
        for record in records
    ] == [
        Resolution.WIN,
        Resolution.WIN,
        Resolution.NONE,
        Resolution.LOSE,
    ]

    # Every outcome references the original wager
    assert all(
        record.wager_outcomes[0].wager_id == original_id
        for record in records
    )

    # Wager removed after seven-out
    assert records[3].wagers_after == ()
    assert wager not in game.wagers

    # Wager identity never changes
    assert wager.id == original_id