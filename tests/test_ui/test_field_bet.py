
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
def field_game(ui_app):
    state = ui_app.states.current

    select_chip(state, 25)

    click(
        state,
        state.get_betting_area("FIELD").rect.center,
    )
    run_until_idle(state)

    wager = state.engine.get_wager(
        state.player,
        WagerType.FIELD,
    )

    assert wager is not None
    assert wager.value == 25
    assert state.player.bankroll == 1475

    return state, wager


@pytest.mark.parametrize(
    "roll,profit",
    [
        (3, 25),   # Even money
        (2, 50),   # Double
        (12, 75),  # Triple
    ],
)
def test_field_wins_and_stays(field_game, roll, profit):
    state, wager = field_game

    sprite = state.wager_sprites[wager]

    force_roll(state, roll)

    # Winning Field wager remains on the table.
    assert wager in state.engine.wagers
    assert wager in state.wager_sprites
    assert state.wager_sprites[wager] is sprite

    assert wager.value == 25
    assert state.player.bankroll == 1475 + profit

    assert (
        state.player_sprite.displayed_bankroll
        == state.player.bankroll
    )


@pytest.mark.parametrize("roll", [5, 6, 7, 8])
def test_field_loses(field_game, roll):
    state, wager = field_game

    force_roll(state, roll)

    assert wager not in state.engine.wagers
    assert wager not in state.wager_sprites

    assert state.player.bankroll == 1475
    assert state.player_sprite.displayed_bankroll == 1475


def test_field_multiple_wins_then_loss(field_game):
    state, wager = field_game

    # Win three consecutive Field rolls.
    for roll in (3, 2, 12):
        force_roll(state, roll)

        assert wager in state.engine.wagers
        assert wager in state.wager_sprites

    # Starting bankroll after placement: $1475
    # Profits: $25 + $50 + $75
    assert state.player.bankroll == 1625

    # Roll 7: lose the original $25 wager.
    force_roll(state, 7)

    assert wager not in state.engine.wagers
    assert wager not in state.wager_sprites

    assert state.player.bankroll == 1625
    assert state.player_sprite.displayed_bankroll == 1625
