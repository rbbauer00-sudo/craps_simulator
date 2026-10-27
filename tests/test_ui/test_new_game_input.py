
import pygame as pg

from ui.states.new_game_state import NewGameState


def key(state, key_code, char="", mod=0):
    state.handle_event(
        pg.event.Event(
            pg.KEYDOWN,
            {
                "key": key_code,
                "unicode": char,
                "mod": mod,
            },
        )
    )


def click_field(state, position):
    state.handle_event(
        pg.event.Event(
            pg.MOUSEBUTTONDOWN,
            {
                "button": 1,
                "pos": position,
            },
        )
    )


def open_setup(ui_app):
    from ui.states.title_state import TitleState

    ui_app.states.reset(TitleState(ui_app))
    ui_app.states.current.start_game()

    setup = ui_app.states.current
    assert isinstance(setup, NewGameState)

    return setup


def test_initial_focus(ui_app):
    setup = open_setup(ui_app)

    assert setup.active_field == "name"
    assert setup.text_selected


def test_typing_replaces_selected_name(ui_app):
    setup = open_setup(ui_app)

    key(setup, pg.K_b, "B")

    assert setup.name == "B"
    assert not setup.text_selected


def test_tab_selects_bankroll(ui_app):
    setup = open_setup(ui_app)

    key(setup, pg.K_TAB)

    assert setup.active_field == "bankroll"
    assert setup.text_selected

    key(setup, pg.K_2, "2")
    key(setup, pg.K_5, "5")
    key(setup, pg.K_0, "0")
    key(setup, pg.K_0, "0")

    assert setup.bankroll_text == "2500"


def test_click_selects_field_text(ui_app):
    setup = open_setup(ui_app)

    click_field(
        setup,
        setup.BANKROLL_RECT.center,
    )

    assert setup.active_field == "bankroll"
    assert setup.text_selected


def test_backspace_removes_selection(ui_app):
    setup = open_setup(ui_app)

    key(setup, pg.K_BACKSPACE)

    assert setup.name == ""
    assert not setup.text_selected


def test_select_all(ui_app):
    setup = open_setup(ui_app)

    key(setup, pg.K_b, "B")
    key(setup, pg.K_a, "a")
    key(setup, pg.K_a, "a", pg.KMOD_CTRL)

    assert setup.text_selected

    key(setup, pg.K_z, "Z")

    assert setup.name == "Z"


def test_bankroll_rejects_letters(ui_app):
    setup = open_setup(ui_app)

    key(setup, pg.K_TAB)
    key(setup, pg.K_a, "a")

    assert setup.bankroll_text == "1500"
    assert setup.text_selected
