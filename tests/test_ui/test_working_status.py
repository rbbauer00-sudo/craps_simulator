
import pytest

from engine import WagerType
from ui.animations import AnimationMode
from ui.input import CursorTool

from .helpers import click, select_chip, run_until_idle


@pytest.mark.parametrize(
    "ui_app",
    list(AnimationMode),
    indirect=True,
)
def test_place_bet_on_off(ui_app):
    state = ui_app.states.current
    state.app.working_preferences.place_on_comeout = True

    # Place a $25 Place 6 wager.
    select_chip(state, 25)
    click(
        state,
        state.get_betting_area("PLACE 6").rect.center
    )
    run_until_idle(state)

    wager = state.engine.get_wager(
        state.player,
        WagerType.PLACE_BET,
        target=6,
    )

    assert wager is not None
    assert wager.is_working is True

    sprite = state.wager_sprites[wager]
    assert sprite.color == (35, 74, 180)

    original_value = wager.value
    original_bankroll = state.player.bankroll


    # Select ON/OFF tool.
    assert not state.is_animating
    assert state.wager_at_position(sprite.rect.center) is wager

    click(
        state,
        state.tool_buttons[CursorTool.ON_OFF].center,
    )

    assert state.selected_tool is CursorTool.ON_OFF

    # First click turns the wager OFF.
    click(state, sprite.rect.center)
    state.update(1 / 60)

    assert wager.is_working is False
    assert sprite.displayed_working is False
    assert sprite.color == (85, 85, 85)

    assert wager.value == original_value
    assert state.player.bankroll == original_bankroll

    # Second click turns the wager back ON.
    # No need to reselect the tool.
    click(state, sprite.rect.center)
    state.update(1 / 60)

    assert wager.is_working is True
    assert sprite.displayed_working is True
    assert sprite.color == (35, 74, 180)

    assert state.selected_tool is CursorTool.ON_OFF
    assert wager.value == original_value
    assert state.player.bankroll == original_bankroll


@pytest.mark.parametrize(
    "ui_app",
    list(AnimationMode),
    indirect=True,
)
def test_pass_line_cannot_be_turned_off(ui_app, capsys):
    state = ui_app.states.current

    select_chip(state, 25)
    click(
        state,
        state.get_betting_area("PASS LINE").rect.center,
    )
    run_until_idle(state)

    wager = state.engine.get_wager(
        state.player,
        WagerType.PASS_LINE,
    )

    assert wager is not None

    sprite = state.wager_sprites[wager]

    original_bankroll = state.player.bankroll

    # Attempt to toggle the Pass Line OFF.
    click(
        state,
        state.tool_buttons[CursorTool.ON_OFF].center,
    )
    click(state, sprite.rect.center)

    # The UI catches GameRuleViolation
    # and reports the rejected operation.
    output = capsys.readouterr().out

    assert "Cannot modify wager:" in output

    # The wager must remain working.
    assert wager.is_working is True
    assert wager in state.engine.wagers
    assert state.player.bankroll == original_bankroll

    state.update(1 / 60)

    assert sprite.displayed_working is True
    assert sprite.color == (35, 74, 180)



def test_chip_selection_clears_on_off_tool(ui_app):
    state = ui_app.states.current

    click(
        state,
        state.tool_buttons[CursorTool.ON_OFF].center,
    )

    assert state.selected_tool is CursorTool.ON_OFF

    select_chip(state, 5)

    assert state.selected_tool is CursorTool.CHIP
    assert state.selected_chip == 5
