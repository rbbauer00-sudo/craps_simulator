
import pytest

from engine import GameSettings, VigSetting, WagerType
from ui.animations import AnimationMode
from ui.input import CursorTool

from .helpers import click, select_chip, run_until_idle


@pytest.mark.parametrize(
    "ui_app",
    list(AnimationMode),
    indirect=True,
)
def test_buy_place_conversion(ui_app):
    state = ui_app.states.current

    # Place $100 on 4.
    select_chip(state, 100)

    click(
        state,
        state.get_betting_area("PLACE 4").rect.center,
    )
    run_until_idle(state)

    wager = state.engine.get_wager(
        state.player,
        WagerType.PLACE_BET,
        target=4,
    )

    assert wager is not None

    # Select BUY tool.
    click(
        state,
        state.tool_buttons[CursorTool.BUY].center,
    )

    # Convert existing Place 4.
    click(
        state,
        state.wager_sprites[wager].rect.center,
    )

    state.update(1 / 60)

    assert wager.is_buy is True
    assert wager in state.wager_sprites
    assert state.wager_sprites[wager].color == (160, 105, 35)

    # Select PLACE tool.
    click(
        state,
        state.tool_buttons[CursorTool.PLACE].center,
    )

    click(
        state,
        state.wager_sprites[wager].rect.center,
    )

    state.update(1 / 60)

    assert wager.is_buy is False
    assert state.wager_sprites[wager].color == (35, 74, 180)
