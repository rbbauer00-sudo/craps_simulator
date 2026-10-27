
import pygame as pg

from ui.states.game_menu_state import GameMenuState

from .helpers import click


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

