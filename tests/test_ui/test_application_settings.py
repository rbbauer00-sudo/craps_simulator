
import pygame as pg
import pytest

from ui.craps_app import CrapsApp
from ui.animations import (
    AnimationMode,
    AnimationSettings,
)
from ui.states.settings_state import SettingsState


def test_settings_from_title():
    app = CrapsApp(start_on_title=True)

    try:
        title = app.states.current

        title.open_settings()

        settings = app.states.current

        assert isinstance(settings, SettingsState)
        assert settings.playing is None
        assert settings.can_change_animation

        settings.select_mode(AnimationMode.INSTANT)

        assert (
            app.animation_settings.mode
            is AnimationMode.INSTANT
        )

        app.states.pop()

        assert app.states.current is title

    finally:
        pg.quit()


def test_title_settings_apply_to_new_game():
    app = CrapsApp(start_on_title=True)

    try:
        title = app.states.current

        title.open_settings()
        settings = app.states.current

        settings.select_mode(AnimationMode.MINIMAL)

        app.states.pop()

        app.new_game()

        playing = app.states.current

        assert (
            app.animation_settings.mode
            is AnimationMode.MINIMAL
        )

        assert (
            playing.wager_animator.settings.mode
            is AnimationMode.MINIMAL
        )

    finally:
        pg.quit()


def test_settings_during_game(ui_app):
    playing = ui_app.states.current

    from ui.states.game_menu_state import GameMenuState

    menu = GameMenuState(ui_app, playing)
    ui_app.states.push(menu)

    menu.open_settings()

    settings = ui_app.states.current

    assert isinstance(settings, SettingsState)
    assert settings.playing is playing

    settings.select_mode(AnimationMode.FULL)

    assert (
        ui_app.animation_settings.mode
        is AnimationMode.FULL
    )

    assert (
        playing.wager_animator.settings.mode
        is AnimationMode.FULL
    )


def test_animation_settings_rejected_during_roll(ui_app):
    playing = ui_app.states.current

    ui_app.set_animation_settings(
        AnimationSettings(mode=AnimationMode.FULL),
        playing_state=playing,
    )

    playing.roll()

    assert playing.is_animating

    from ui.states.game_menu_state import GameMenuState

    menu = GameMenuState(ui_app, playing)
    ui_app.states.push(menu)

    menu.open_settings()
    settings = ui_app.states.current

    assert not settings.can_change_animation

    settings.select_mode(AnimationMode.INSTANT)

    assert (
        ui_app.animation_settings.mode
        is AnimationMode.FULL
    )

    with pytest.raises(RuntimeError):
        ui_app.set_animation_settings(
            AnimationSettings(mode=AnimationMode.INSTANT),
            playing_state=playing,
        )
