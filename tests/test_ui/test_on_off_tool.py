
import pytest

from engine import defs
from ui.input import CursorTool

from .helpers import click, run_until_idle


def place_six(playing):
    playing.change_wager(
        30,
        definition=defs.PLACE_BET,
        target=6,
        position=(290, 350),
    )

    run_until_idle(playing)

    return next(
        wager
        for wager in playing.engine.wagers
        if wager.definition is defs.PLACE_BET
        and wager.target == 6
    )


def test_on_off_selector_exists(ui_app):
    playing = ui_app.states.current

    assert CursorTool.ON_OFF in playing.tool_buttons

    click(
        playing,
        playing.tool_buttons[
            CursorTool.ON_OFF
        ].center,
    )

    assert playing.selected_tool is CursorTool.ON_OFF


def test_on_off_toggles_wager(ui_app):
    playing = ui_app.states.current
    playing.app.working_preferences.place_on_comeout = True
    wager = place_six(playing)

    click(
        playing,
        playing.tool_buttons[
            CursorTool.ON_OFF
        ].center,
    )

    assert wager.is_working

    click(
        playing,
        playing.wager_sprites[wager].rect.center,
    )

    assert not wager.is_working
    assert playing.selected_tool is CursorTool.ON_OFF

    click(
        playing,
        playing.wager_sprites[wager].rect.center,
    )

    assert wager.is_working


def test_right_click_does_not_toggle(ui_app):
    playing = ui_app.states.current
    playing.app.working_preferences.place_on_comeout = True
    wager = place_six(playing)

    click(
        playing,
        playing.tool_buttons[
            CursorTool.ON_OFF
        ].center,
    )

    click(
        playing,
        playing.wager_sprites[wager].rect.center,
        button=3,
    )

    assert wager.is_working


def test_ineligible_wager_rejected(ui_app):
    playing = ui_app.states.current

    playing.change_wager(
        25,
        definition=defs.FIELD,
        position=(95, 525),
    )

    run_until_idle(playing)

    wager = next(
        wager
        for wager in playing.engine.wagers
        if wager.definition is defs.FIELD
    )

    click(
        playing,
        playing.tool_buttons[
            CursorTool.ON_OFF
        ].center,
    )

    # UI catches the engine's rule violation.
    click(
        playing,
        playing.wager_sprites[wager].rect.center,
    )

    assert wager.is_working
