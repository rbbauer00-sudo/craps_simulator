
import pygame as pg

from ui.craps_app import CrapsApp
from ui.states.title_state import TitleState
from ui.states.playing_state import PlayingState


def test_title_is_initial_state():
    app = CrapsApp(start_on_title=True)

    try:
        assert isinstance(
            app.states.current,
            TitleState,
        )

        assert not app.engine.wagers

    finally:
        pg.quit()


def test_new_game_from_title():
    app = CrapsApp(start_on_title=True)

    try:
        title = app.states.current
        original_engine = app.engine

        title.handle_event(
            pg.event.Event(
                pg.MOUSEBUTTONDOWN,
                {
                    "button": 1,
                    "pos": title.NEW_GAME_BUTTON.center,
                },
            )
        )

        assert isinstance(
            app.states.current,
            PlayingState,
        )

        assert app.engine is not original_engine
        assert app.engine.point is None
        assert not app.engine.wagers

    finally:
        pg.quit()


def test_quit_from_title():
    app = CrapsApp(start_on_title=True)

    try:
        title = app.states.current
        app.running = True

        title.handle_event(
            pg.event.Event(
                pg.MOUSEBUTTONDOWN,
                {
                    "button": 1,
                    "pos": title.QUIT_BUTTON.center,
                },
            )
        )

        assert not app.running

    finally:
        pg.quit()
