
from ui.states.settings_state import SettingsState
from ui.states.animation_settings_state import (
    AnimationSettingsState,
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
