
from ui.states.settings_state import SettingsState
from ui.states.animation_settings_state import (
    AnimationSettingsState,
)
from ui.states.player_preferences_state import (
    PlayerPreferencesState,
)
from .helpers import click


def test_settings_opens_animation(ui_app):
    app = ui_app
    playing = app.states.current

    settings = SettingsState(app, playing)
    app.states.push(settings)

    assert app.states.current is settings

    click(
        settings,
        settings.ANIMATION_BUTTON.center,
    )

    assert isinstance(
        app.states.current,
        AnimationSettingsState,
    )

    assert app.states.current.playing is playing


def test_back_returns_to_settings(ui_app):
    app = ui_app
    playing = app.states.current

    settings = SettingsState(app, playing)
    app.states.push(settings)

    click(
        settings,
        settings.ANIMATION_BUTTON.center,
    )

    animation = app.states.current

    click(
        animation,
        animation.BACK_BUTTON.center,
    )

    assert app.states.current is settings


def test_settings_back_returns_to_game(ui_app):
    app = ui_app
    playing = app.states.current

    settings = SettingsState(app, playing)
    app.states.push(settings)

    click(
        settings,
        settings.BACK_BUTTON.center,
    )

    assert app.states.current is playing



def test_settings_opens_player_preferences(ui_app):
    app = ui_app
    playing = app.states.current

    settings = SettingsState(app, playing)
    app.states.push(settings)

    click(
        settings,
        settings.PLAYER_PREFERENCES_BUTTON.center,
    )

    preferences = app.states.current

    assert isinstance(
        preferences,
        PlayerPreferencesState,
    )
    assert preferences.playing is playing


def test_player_preferences_back_to_settings(ui_app):
    app = ui_app
    playing = app.states.current

    settings = SettingsState(app, playing)
    app.states.push(settings)

    click(
        settings,
        settings.PLAYER_PREFERENCES_BUTTON.center,
    )

    preferences = app.states.current

    click(
        preferences,
        preferences.BACK_BUTTON.center,
    )

    assert app.states.current is settings


def test_player_preferences_preserves_game(ui_app):
    app = ui_app
    playing = app.states.current
    original_engine = app.engine

    settings = SettingsState(app, playing)
    app.states.push(settings)

    click(
        settings,
        settings.PLAYER_PREFERENCES_BUTTON.center,
    )

    preferences = app.states.current

    # Disabled entries should not open anything yet.
    click(
        preferences,
        preferences.WAGER_BEHAVIOR_BUTTON.center,
    )
    assert app.states.current is preferences

    click(
        preferences,
        preferences.WORKING_STATUS_BUTTON.center,
    )
    assert app.states.current is preferences

    click(
        preferences,
        preferences.BACK_BUTTON.center,
    )
    click(
        settings,
        settings.BACK_BUTTON.center,
    )

    assert app.states.current is playing
    assert app.engine is original_engine
