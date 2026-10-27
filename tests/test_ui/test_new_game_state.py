
import pygame as pg

from ui.craps_app import CrapsApp
from ui.states.new_game_state import NewGameState
from ui.states.playing_state import PlayingState
from ui.states.title_state import TitleState


def test_new_game_setup_starts_game():
    app = CrapsApp(start_on_title=True)

    try:
        title = app.states.current
        title.start_game()

        setup = app.states.current
        assert isinstance(setup, NewGameState)

        setup.name = "Test Player"
        setup.bankroll_text = "2500"

        setup.start_game()

        assert isinstance(
            app.states.current,
            PlayingState,
        )

        player = app.engine.players[0]

        assert player.name == "Test Player"
        assert player.bankroll == 2500

    finally:
        pg.quit()


def test_invalid_bankroll_does_not_start():
    app = CrapsApp(start_on_title=True)

    try:
        app.states.current.start_game()
        setup = app.states.current

        setup.bankroll_text = "0"
        setup.start_game()

        assert app.states.current is setup
        assert setup.error

    finally:
        pg.quit()


def test_back_returns_to_title():
    app = CrapsApp(start_on_title=True)

    try:
        title = app.states.current
        title.start_game()

        setup = app.states.current
        setup.go_back()

        assert app.states.current is title
        assert isinstance(
            app.states.current,
            TitleState,
        )

    finally:
        pg.quit()
