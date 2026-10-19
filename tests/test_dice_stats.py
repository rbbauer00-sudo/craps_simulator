
from engine import Game
from simulator import Simulator, DiceStatistics


def test_dice_statistics():
    game = Game(predetermined_rolls=[
        (1, 1),  # 2
        (2, 2),  # 4 hard
        (3, 3),  # 6 hard
        (1, 6),  # 7
        (3, 4),  # 7
        (5, 5),  # 10 hard
    ])

    game.add_player()
    sim = Simulator(game)
    sim.run(6)

    stats = DiceStatistics(sim.recorder.rolls)

    assert stats.total_rolls == 6

    assert stats.total_frequencies == {
        2: 1,
        4: 1,
        6: 1,
        7: 2,
        10: 1,
    }

    assert stats.seven_count == 2
    assert stats.hardway_count == 3

    assert stats.combination_frequencies[(1, 6)] == 1
    assert stats.combination_frequencies[(3, 4)] == 1
    assert stats.combination_frequencies[(2, 2)] == 1

    assert stats.expected_count(7) == 1.0
