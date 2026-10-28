
from engine import WagerType
from ui.animations import AnimationMode, AnimationSettings
from ui.states.working_status_state import WorkingStatusState

from .helpers import click, select_chip, run_until_idle

import pygame as pg

from ui.craps_app import CrapsApp
from ui.states.settings_state import SettingsState
from ui.states.player_preferences_state import PlayerPreferencesState


def test_working_preferences_from_title():
    app = CrapsApp(start_on_title=True)

    try:
        title = app.states.current
        title.open_settings()

        settings = app.states.current
        assert isinstance(settings, SettingsState)

        click(
            settings,
            settings.PLAYER_PREFERENCES_BUTTON.center,
        )

        preferences = app.states.current
        assert isinstance(preferences, PlayerPreferencesState)

        click(
            preferences,
            preferences.WORKING_STATUS_BUTTON.center,
        )

        working = app.states.current
        assert isinstance(working, WorkingStatusState)

        click(working, working.PLACE_BUTTON.center)

        assert app.working_preferences.place_on_comeout

        app.new_game()

        assert app.working_preferences.place_on_comeout

    finally:
        pg.quit()


def open_working(ui_app, playing=None):
    state = WorkingStatusState(ui_app, playing)
    ui_app.states.push(state)
    return state


def place_six(playing):
    select_chip(playing, 25)

    click(
        playing,
        playing.get_betting_area("PLACE 6").rect.center,
    )

    run_until_idle(playing)

    return playing.engine.get_wager(
        playing.player,
        WagerType.PLACE_BET,
        target=6,
    )


def test_default_preferences(ui_app):
    state = open_working(ui_app)

    assert not ui_app.working_preferences.place_on_comeout
    assert ui_app.working_preferences.hardway_on_comeout
    assert state.can_change_working


def test_toggle_preferences(ui_app):
    state = open_working(ui_app)

    click(state, state.PLACE_BUTTON.center)

    assert ui_app.working_preferences.place_on_comeout

    click(state, state.HARDWAY_BUTTON.center)

    assert not ui_app.working_preferences.hardway_on_comeout

    click(state, state.PLACE_BUTTON.center)

    assert not ui_app.working_preferences.place_on_comeout


def test_preferences_survive_new_game(ui_app):
    state = open_working(ui_app)

    click(state, state.PLACE_BUTTON.center)

    preferences = ui_app.working_preferences

    ui_app.new_game()

    assert ui_app.working_preferences is preferences
    assert preferences.place_on_comeout


def test_existing_wager_updates_immediately(ui_app):
    playing = ui_app.states.current
    wager = place_six(playing)

    assert wager is not None
    assert not wager.is_working

    state = open_working(ui_app, playing)

    click(state, state.PLACE_BUTTON.center)

    assert ui_app.working_preferences.place_on_comeout
    assert wager.is_working

    click(state, state.PLACE_BUTTON.center)

    assert not wager.is_working


def test_manual_override_is_preserved(ui_app):
    playing = ui_app.states.current
    wager = place_six(playing)

    # Manually turn the wager ON.
    playing.set_manual_working_status(wager)

    assert wager.is_working
    assert wager in playing.manual_working_overrides

    state = open_working(ui_app, playing)

    # Change automatic defaults twice.
    click(state, state.PLACE_BUTTON.center)
    click(state, state.PLACE_BUTTON.center)

    # Manual status must remain unchanged.
    assert wager.is_working


def test_rejected_during_animation(ui_app):
    playing = ui_app.states.current

    ui_app.set_animation_settings(
        AnimationSettings(mode=AnimationMode.FULL),
        playing_state=playing,
    )

    playing.roll()
    assert playing.is_animating

    state = open_working(ui_app, playing)

    assert not state.can_change_working

    click(state, state.PLACE_BUTTON.center)

    assert not ui_app.working_preferences.place_on_comeout

    click(state, state.HARDWAY_BUTTON.center)

    assert ui_app.working_preferences.hardway_on_comeout


