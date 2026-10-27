
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
def hardway_game(ui_app, request):
    state = ui_app.states.current

    number = request.param

    select_chip(state, 25)

    click(
        state,
        state.get_betting_area(
            f"HARD {number}"
        ).rect.center,
    )
    run_until_idle(state)

    wager = state.engine.get_wager(
        state.player,
        WagerType.HARDWAY,
        target=number,
    )

    assert wager is not None
    assert wager.value == 25
    assert state.player.bankroll == 1475

    return state, wager


@pytest.mark.parametrize(
    "hardway_game,roll,profit",
    [
        (4, (2, 2), 175),
        (6, (3, 3), 225),
        (8, (4, 4), 225),
        (10, (5, 5), 175),
    ],
    indirect=["hardway_game"],
)
def test_hardway_wins_and_stays(
    hardway_game,
    roll,
    profit,
):
    state, wager = hardway_game

    sprite = state.wager_sprites[wager]

    # Forced individual dice are essential:
    # total alone cannot distinguish hard/soft.
    for char in f"{roll[0]},{roll[1]}":
        state.forced_roll_buffer.add(char)

    state.roll()
    run_until_idle(state)

    assert wager in state.engine.wagers
    assert wager in state.wager_sprites
    assert state.wager_sprites[wager] is sprite

    assert state.player.bankroll == 1475 + profit
    assert (
        state.player_sprite.displayed_bankroll
        == state.player.bankroll
    )


@pytest.mark.parametrize(
    "hardway_game,roll",
    [
        (4, (1, 3)),
        (6, (2, 4)),
        (8, (3, 5)),
        (10, (4, 6)),
    ],
    indirect=["hardway_game"],
)
def test_hardway_loses_on_soft_number(
    hardway_game,
    roll,
):
    state, wager = hardway_game

    for char in f"{roll[0]},{roll[1]}":
        state.forced_roll_buffer.add(char)

    state.roll()
    run_until_idle(state)

    assert wager not in state.engine.wagers
    assert wager not in state.wager_sprites

    assert state.player.bankroll == 1475
    assert state.player_sprite.displayed_bankroll == 1475


@pytest.mark.parametrize(
    "hardway_game",
    [4, 6, 8, 10],
    indirect=True,
)
def test_hardway_loses_on_seven(hardway_game):
    state, wager = hardway_game

    force_roll(state, 7)

    assert wager not in state.engine.wagers
    assert wager not in state.wager_sprites

    assert state.player.bankroll == 1475
    assert state.player_sprite.displayed_bankroll == 1475


@pytest.mark.parametrize(
    "hardway_game",
    [4, 6, 8, 10],
    indirect=True,
)
def test_hardway_unaffected_by_other_number(
    hardway_game,
):
    state, wager = hardway_game

    force_roll(state, 5)

    assert wager in state.engine.wagers
    assert wager in state.wager_sprites
    assert wager.value == 25
    assert state.player.bankroll == 1475
