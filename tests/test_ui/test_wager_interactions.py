
from engine import WagerType
from .helpers import click, select_chip, run_until_idle

import pytest
from ui.animations import AnimationMode


@pytest.mark.parametrize(
    "ui_app",
    list(AnimationMode),
    indirect=True,
)


def test_place_increase_decrease_and_remove(ui_app):
    state = ui_app.states.current

    area = state.betting_areas[WagerType.PLACE_BET]

    select_chip(state, 25)
    click(state, area.center)
    run_until_idle(state)

    wager = state.engine.get_wager(
        state.player,
        WagerType.PLACE_BET,
        target=6,
    )

    assert wager is not None
    assert wager.value == 25

    select_chip(state, 5)
    click(state, state.wager_sprites[wager].rect.center)
    run_until_idle(state)

    assert wager.value == 30

    click(
        state,
        state.wager_sprites[wager].rect.center,
        button=3,
    )
    run_until_idle(state)

    assert wager.value == 25

    select_chip(state, 100)
    click(
        state,
        state.wager_sprites[wager].rect.center,
        button=3,
    )
    run_until_idle(state)

    assert wager not in state.engine.wagers
    assert wager not in state.wager_sprites
