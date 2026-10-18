from engine import Game
from simulator import Statistics

def test_statistics_roll_tracking():
    stats = Statistics()

    game = Game(predetermined_rolls=[
        (2, 2),  # Point 4 established
        (1, 3),  # Point 4 made
        (3, 3),  # Point 6 established
        (1, 6),  # Seven-out
    ])

    for _ in range(4):
        result = game.roll()
        stats.record_roll(result)

    assert stats.roll_count == 4
    assert stats.roll_frequencies[4] == 2
    assert stats.roll_frequencies[6] == 1
    assert stats.roll_frequencies[7] == 1
    assert stats.points_made == 1
    assert stats.seven_outs == 1