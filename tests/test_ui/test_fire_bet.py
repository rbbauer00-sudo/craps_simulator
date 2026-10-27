
import pytest

from engine import WagerType
from ui.animations import AnimationMode

from .helpers import (
    click,
    select_chip,
    run_until_idle,
    force_roll,
)


pytestmark = pytest.mark.parametrize(
    "ui_app",
    list(AnimationMode),
    indirect=True,
)


@pytest.fixture
def fire_game(ui_app):
    state = ui_app.states.current

    select_chip(state, 5)
    click(
        state,
        state.get_betting_area("FIRE").rect.center,
    )
    run_until_idle(state)

    wager = next(
        w for w in state.engine.wagers
        if w.definition.wager_type is WagerType.FIRE_BET
    )

    assert wager.value == 5
    assert wager.targets_hit == set()
    assert state.player.bankroll == 1495

    return state, wager


def make_point(state, number):
    """Establish a point, then make it."""
    assert state.engine.point is None

    force_roll(state, number)
    assert state.engine.point == number

    force_roll(state, number)
    assert state.engine.point is None


@pytest.mark.parametrize(
    "points,multiple",
    [
        ((4, 5, 6, 8), 24),
        ((4, 5, 6, 8, 9), 249),
    ],
)
def test_fire_wins_on_seven_out(
    fire_game,
    points,
    multiple,
):
    state, wager = fire_game

    for number in points:
        make_point(state, number)

        assert wager.targets_hit == set(
            points[:points.index(number) + 1]
        )

    # Establish another point, then seven out.
    force_roll(state, 10)
    assert state.engine.point == 10

    force_roll(state, 7)

    assert wager not in state.engine.wagers
    assert wager not in state.wager_sprites

    expected = 1500 + 5 * multiple

    assert state.player.bankroll == expected
    assert (
        state.player_sprite.displayed_bankroll
        == expected
    )


def test_fire_wins_on_sixth_point(fire_game):
    state, wager = fire_game

    for number in (4, 5, 6, 8, 9):
        make_point(state, number)

    assert len(wager.targets_hit) == 5
    assert wager in state.engine.wagers

    # Sixth distinct completed point.
    make_point(state, 10)

    assert wager.targets_hit == {4, 5, 6, 8, 9, 10}
    assert wager not in state.engine.wagers
    assert wager not in state.wager_sprites

    expected = 1500 + 5 * 999

    assert state.player.bankroll == expected
    assert (
        state.player_sprite.displayed_bankroll
        == expected
    )


@pytest.mark.parametrize(
    "points",
    [
        (),
        (4,),
        (4, 5),
        (4, 5, 6),
    ],
)
def test_fire_loses_with_fewer_than_four_points(
    fire_game,
    points,
):
    state, wager = fire_game

    for number in points:
        make_point(state, number)

    assert wager.targets_hit == set(points)

    # Establish another point, then seven out.
    force_roll(state, 10)
    force_roll(state, 7)

    assert wager not in state.engine.wagers
    assert wager not in state.wager_sprites

    assert state.player.bankroll == 1495
    assert state.player_sprite.displayed_bankroll == 1495


def test_fire_does_not_count_repeated_points(fire_game):
    state, wager = fire_game

    make_point(state, 4)
    make_point(state, 4)
    make_point(state, 6)

    assert wager.targets_hit == {4, 6}
    assert len(wager.targets_hit) == 2

    assert wager in state.engine.wagers
    assert state.player.bankroll == 1495
