
import pygame as pg

from ui.states.game_menu_state import GameMenuState
from ui.states.new_game_state import NewGameState
from .helpers import click
#from engine import WagerType
from ui.animations import AnimationMode, AnimationSettings
from ui.states.playing_state import PlayingState
from ui.states.settings_state import SettingsState




def press_escape(state):
    state.handle_event(
        pg.event.Event(
            pg.KEYDOWN,
            {"key": pg.K_ESCAPE},
        )
    )


def test_escape_opens_pause_menu(ui_app):
    playing = ui_app.states.current

    press_escape(playing)

    menu = ui_app.states.current

    assert isinstance(menu, GameMenuState)
    assert menu.transparent
    assert menu is not playing

    assert ui_app.states._stack[-2] is playing


def test_escape_resumes_game(ui_app):
    playing = ui_app.states.current

    press_escape(playing)

    menu = ui_app.states.current
    press_escape(menu)

    assert ui_app.states.current is playing


def test_resume_button(ui_app):
    playing = ui_app.states.current

    press_escape(playing)

    menu = ui_app.states.current

    click(menu, menu.RESUME_BUTTON.center)

    assert ui_app.states.current is playing


def test_game_is_frozen_while_paused(ui_app):
    playing = ui_app.states.current
    bankroll_before = playing.player.bankroll
    point_before = playing.engine.point

    press_escape(playing)

    # Events go to GameMenuState, not PlayingState.
    ui_app.states.handle_event(
        pg.event.Event(
            pg.KEYDOWN,
            {
                "key": pg.K_RETURN,
                "unicode": "\r",
            },
        )
    )

    ui_app.states.update(1 / 60)

    assert playing.player.bankroll == bankroll_before
    assert playing.engine.point == point_before
    assert playing.current_roll is None


def test_quit_button(ui_app):
    playing = ui_app.states.current

    press_escape(playing)
    menu = ui_app.states.current

    ui_app.running = True

    click(menu, menu.QUIT_BUTTON.center)

    assert not ui_app.running


import pygame as pg
import pytest

from ui.animations import AnimationMode
from ui.states.game_menu_state import GameMenuState

from .helpers import run_until_idle


def escape(app):
    app.states.handle_event(
        pg.event.Event(
            pg.KEYDOWN,
            {"key": pg.K_ESCAPE},
        )
    )


def test_menu_opens_and_resumes(ui_app):
    playing = ui_app.states.current

    escape(ui_app)
    assert isinstance(
        ui_app.states.current, GameMenuState
    )

    escape(ui_app)
    assert ui_app.states.current is playing


@pytest.mark.parametrize(
    "ui_app",
    [
        AnimationMode.FULL,
        AnimationMode.SIMULTANEOUS,
        AnimationMode.MINIMAL,
    ],
    indirect=True,
)
def test_menu_freezes_active_animation(ui_app):
    playing = ui_app.states.current

    # Trigger an actual dice animation.
    playing.roll()

    assert playing.is_animating

    # Advance partway through it.
    ui_app.states.update(0.1)

    phase_before = playing.roll_phase
    dice_elapsed_before = (
        playing.dice_sprite.animation_elapsed
    )

    # Open the menu while animation is running.
    escape(ui_app)

    assert isinstance(
        ui_app.states.current, GameMenuState
    )
    assert playing.is_animating

    # The state stack must not advance PlayingState.
    for _ in range(30):
        ui_app.states.update(1 / 60)

    assert playing.roll_phase is phase_before
    assert (
        playing.dice_sprite.animation_elapsed
        == dice_elapsed_before
    )

    # Resume.
    escape(ui_app)

    assert ui_app.states.current is playing

    # Animation continues from its saved position.
    ui_app.states.update(1 / 60)

    assert (
        playing.dice_sprite.animation_elapsed
        > dice_elapsed_before
    )

    run_until_idle(playing)

    assert not playing.is_animating
    assert playing.current_roll is None





def test_new_game_resets_engine(ui_app):
    playing = ui_app.states.current

    original_engine = ui_app.engine
    original_settings = original_engine.settings

    press_escape(playing)
    menu = ui_app.states.current

    click(menu, menu.NEW_GAME_BUTTON.center)

    setup = ui_app.states.current

    assert isinstance(setup, NewGameState)

    # Opening setup must preserve the old session.
    assert ui_app.engine is original_engine
    assert setup.game_settings == original_settings

    setup.name = "New Player"
    setup.bankroll_text = "2500"

    click(setup, setup.START_BUTTON.center)

    assert ui_app.engine is not original_engine
    assert ui_app.engine.settings == original_settings

    assert isinstance(
        ui_app.states.current,
        PlayingState,
    )

    assert ui_app.states.current is not playing
    assert ui_app.engine.point is None
    assert not ui_app.engine.wagers

    player = ui_app.engine.players[0]

    assert player.name == "New Player"
    assert player.bankroll == 2500


def test_settings_change_animation_mode(ui_app):
    playing = ui_app.states.current

    press_escape(playing)
    menu = ui_app.states.current

    click(menu, menu.SETTINGS_BUTTON.center)

    settings = ui_app.states.current
    assert isinstance(settings, SettingsState)

    click(
        settings,
        settings.mode_buttons[AnimationMode.FULL].center,
    )

    assert (
        ui_app.animation_settings.mode
        is AnimationMode.FULL
    )
    assert (
        playing.wager_animator.settings.mode
        is AnimationMode.FULL
    )

    click(settings, settings.BACK_BUTTON.center)

    assert ui_app.states.current is menu


def test_settings_disabled_during_animation(ui_app):
    playing = ui_app.states.current

    # INSTANT completes synchronously, so switch first.
    ui_app.set_animation_settings(
        ui_app.animation_settings.__class__(
            mode=AnimationMode.FULL,
        )
    )

    playing.roll()
    assert playing.is_animating

    press_escape(playing)
    menu = ui_app.states.current

    assert menu.can_start_new_game


    click(menu, menu.SETTINGS_BUTTON.center)

    settings = ui_app.states.current
    assert isinstance(settings, SettingsState)
    assert not settings.can_change_animation

    click(
        settings,
        settings.mode_buttons[
            AnimationMode.INSTANT
        ].center,
    )

    # Changing mode must be rejected.
    assert (
        ui_app.animation_settings.mode
        is AnimationMode.FULL
    )

    # Return to the menu and resume the same roll.
    click(settings, settings.BACK_BUTTON.center)
    assert ui_app.states.current is menu

    click(menu, menu.RESUME_BUTTON.center)

    assert ui_app.states.current is playing
    assert playing.is_animating



def test_cancel_new_game_preserves_session(ui_app):
    playing = ui_app.states.current
    original_engine = ui_app.engine

    press_escape(playing)
    menu = ui_app.states.current

    click(menu, menu.NEW_GAME_BUTTON.center)

    setup = ui_app.states.current

    assert isinstance(setup, NewGameState)

    # Change pending options.
    setup.bankroll_text = "5000"

    # Cancel.
    click(setup, setup.BACK_BUTTON.center)

    assert ui_app.states.current is menu
    assert ui_app.engine is original_engine

    # Resume original session.
    click(menu, menu.RESUME_BUTTON.center)

    assert ui_app.states.current is playing
    assert ui_app.engine is original_engine



def test_new_game_during_animation(ui_app):
    playing = ui_app.states.current

    ui_app.set_animation_settings(
        AnimationSettings(mode=AnimationMode.FULL),
        playing_state=playing,
    )

    playing.roll()
    assert playing.is_animating

    original_engine = ui_app.engine

    press_escape(playing)
    menu = ui_app.states.current

    click(menu, menu.NEW_GAME_BUTTON.center)

    setup = ui_app.states.current
    assert isinstance(setup, NewGameState)

    # Starting setup must not interrupt the old roll.
    assert ui_app.engine is original_engine
    assert playing.is_animating

    click(setup, setup.START_BUTTON.center)

    # The old animation and states are discarded.
    assert ui_app.engine is not original_engine
    assert isinstance(
        ui_app.states.current,
        PlayingState,
    )

    assert not ui_app.states.current.is_animating



def test_cancel_new_game_during_animation(ui_app):
    playing = ui_app.states.current

    ui_app.set_animation_settings(
        AnimationSettings(mode=AnimationMode.FULL),
        playing_state=playing,
    )

    playing.roll()
    assert playing.is_animating

    press_escape(playing)
    menu = ui_app.states.current

    click(menu, menu.NEW_GAME_BUTTON.center)
    setup = ui_app.states.current

    click(setup, setup.BACK_BUTTON.center)
    assert ui_app.states.current is menu

    click(menu, menu.RESUME_BUTTON.center)

    assert ui_app.states.current is playing
    assert playing.is_animating
