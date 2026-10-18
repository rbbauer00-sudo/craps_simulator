
import pytest

from engine import Game, WagerType
from simulator import Simulator, PassLineStrategy


BET_AMOUNT = 25
STARTING_BANKROLL = 1500

@pytest.fixture
def sim_setup():
    def create_simulator(rolls=None, bankroll=1500):
        game = Game(predetermined_rolls=rolls)
        player = game.add_player(bankroll=bankroll)

        strategy = PassLineStrategy(player, BET_AMOUNT)
        simulator = Simulator(game, strategy)

        return simulator, game, player
    
    return create_simulator


# =======================
# INITIAL PLACEMENT
# =======================

def test_simulator_places_initial_pass_line(sim_setup):
    predetermined_rolls = [(2, 2)]

    simulator, game, player = sim_setup(predetermined_rolls)
    simulator.step()

    wager = game.get_wager(
        player, WagerType.PASS_LINE, None
    )

    assert wager is not None
    assert wager.value == BET_AMOUNT
    assert player.bankroll == STARTING_BANKROLL - BET_AMOUNT
    assert simulator.roll_count == 1


# =======================
# DUPLICATE PREVENTION
# =======================

def test_simulator_does_not_duplicate_pass_line(sim_setup):
    predetermined_rolls = [
    (2, 2), # Establish point 4
    (2, 3), # Roll 5
]
   
    simulator, game, player = sim_setup(predetermined_rolls)

    simulator.run(2)

    wagers = [
        w for w in game.wagers
        if w.player is player
        and w.definition.wager_type is WagerType.PASS_LINE
    ]

    assert len(wagers) == 1
    assert game.point == 4
    assert player.bankroll == STARTING_BANKROLL - BET_AMOUNT
    assert simulator.roll_count == 2


# =======================
# REPLACE AFTER LOSS
# =======================

def test_simulator_replaces_pass_line_after_loss(sim_setup):

    predetermined_rolls = [
        (1, 2),  # Come-out 3: Pass Line loses
        (2, 3),  # Establish point 5
    ]
    simulator, game, player = sim_setup(predetermined_rolls)

    simulator.step()

    assert game.point is None
    assert game.get_wager(
        player, WagerType.PASS_LINE, None
    ) is None
    assert player.bankroll == STARTING_BANKROLL - BET_AMOUNT

    simulator.step()

    assert game.point == 5
    assert game.get_wager(
        player, WagerType.PASS_LINE, None
    ) is not None
    assert player.bankroll == STARTING_BANKROLL - 2 * BET_AMOUNT


# =======================
# COMPLETE LIFECYCLE
# =======================

def test_simulator_pass_line_lifecycle(sim_setup):

    predetermined_rolls = [
        (2, 2),  # 4: Establish point
        (1, 3),  # 4: Point winner
        (1, 2),  # 3: Come-out loser
        (5, 6),  # 11: Come-out winner
        (3, 3),  # 6: Establish point
        (1, 6),  # 7: Seven-out
    ]

    simulator, game, player = sim_setup(predetermined_rolls)
    simulator.run(6)

    # Starting bankroll: 1500
    # Point winner:       +25
    # Come-out loser:     -25
    # Come-out winner:    +25
    # Seven-out:         -25
    #
    # Final bankroll:    1500

    assert simulator.roll_count == 6
    assert game.point is None
    assert player.bankroll == STARTING_BANKROLL
    assert not game.wagers


# =======================
# ROLL COUNT
# =======================

@pytest.mark.parametrize("num_rolls", [1, 10, 100])
def test_simulator_roll_count(sim_setup, num_rolls):
    simulator, game, player = sim_setup()

    simulator.run(num_rolls)

    assert simulator.roll_count == num_rolls
