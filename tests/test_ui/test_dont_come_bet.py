
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
def dont_come_game(ui_app):
    state = ui_app.states.current

    # Establish table point 4.
    force_roll(state, 4)

    assert state.engine.point == 4

    # Place a $25 Don't Come bet.
    select_chip(state, 25)

    click(
        state,
        state.get_betting_area("DON'T COME").rect.center,
    )
    run_until_idle(state)

    wager = state.engine.get_wager(
        state.player,
        WagerType.DONT_COME,
        target=None,
    )

    assert wager is not None
    assert wager.value == 25

    return state, wager


def test_dont_come_travels(dont_come_game):
    state, wager = dont_come_game

    sprite = state.wager_sprites[wager]

    force_roll(state, 6)

    assert wager.target == 6
    assert wager in state.engine.wagers
    assert state.wager_sprites[wager] is sprite

    assert sprite.rect.center == pytest.approx(
        state.layout.DONT_COME_POSITIONS[6],
        abs=1,
    )

    assert state.player.bankroll == 1475


def test_dont_come_wins_on_seven(dont_come_game):
    state, wager = dont_come_game

    force_roll(state, 6)
    force_roll(state, 7)

    assert state.engine.point is None

    assert wager not in state.engine.wagers
    assert wager not in state.wager_sprites

    # $25 stake returned plus $25 profit.
    assert state.player.bankroll == 1525
    assert state.player_sprite.displayed_bankroll == 1525


def test_dont_come_loses_on_number(dont_come_game):
    state, wager = dont_come_game

    force_roll(state, 6)
    force_roll(state, 6)

    assert wager not in state.engine.wagers
    assert wager not in state.wager_sprites

    assert state.player.bankroll == 1475
    assert state.player_sprite.displayed_bankroll == 1475


def test_dont_come_odds_placement(dont_come_game):
    state, parent = dont_come_game

    # Travel Don't Come to 6.
    force_roll(state, 6)

    odds_area = state.get_betting_area("DC 6 ODDS")

    select_chip(state, 25)
    click(state, odds_area.rect.center)
    run_until_idle(state)

    odds = state.engine.get_child_wager(parent)

    assert odds is not None
    assert odds.parent_wager is parent
    assert odds.value == 25
    assert odds.target == 6
    assert odds in state.engine.wagers
    assert odds in state.wager_sprites


@pytest.mark.parametrize(
    "final_roll,expected_bankroll",
    [
        (7, 1545),
        (6, 1450),
    ],
)
def test_dont_come_odds_resolution(
    dont_come_game,
    final_roll,
    expected_bankroll,
):
    state, parent = dont_come_game

    # Travel Don't Come to 6.
    force_roll(state, 6)

    assert parent.target == 6

    # Place $25 lay odds.
    select_chip(state, 25)

    click(
        state,
        state.get_betting_area("DC 6 ODDS").rect.center,
    )
    run_until_idle(state)

    odds = state.engine.get_child_wager(parent)

    assert odds is not None
    assert odds.value == 25
    assert odds.parent_wager is parent

    # Resolve the parent and its odds.
    force_roll(state, final_roll)

    assert parent not in state.engine.wagers
    assert odds not in state.engine.wagers

    assert parent not in state.wager_sprites
    assert odds not in state.wager_sprites

    assert state.player.bankroll == expected_bankroll
    assert (
        state.player_sprite.displayed_bankroll
        == expected_bankroll
    )

    assert not state.is_animating
    assert state.current_roll is None
