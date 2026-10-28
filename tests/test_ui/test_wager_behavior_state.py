
from engine import WagerType

from ui.states.new_game_state import NewGameState
from ui.states.wager_behavior_state import WagerBehaviorState

from .helpers import click


def open_behavior(ui_app):
    ui_app.states.current.start_game()

    setup = ui_app.states.current
    assert isinstance(setup, NewGameState)

    click(setup, setup.BEHAVIOR_BUTTON.center)

    behavior = ui_app.states.current
    assert isinstance(behavior, WagerBehaviorState)

    return setup, behavior


def test_default_stay_up(ui_app):
    from ui.states.title_state import TitleState

    ui_app.states.reset(TitleState(ui_app))

    setup, behavior = open_behavior(ui_app)

    for wager_type, _ in behavior.WAGER_TYPES:
        assert not behavior.take_down(wager_type)


def test_toggle_wager_behavior(ui_app):
    from ui.states.title_state import TitleState

    ui_app.states.reset(TitleState(ui_app))

    setup, behavior = open_behavior(ui_app)

    click(
        behavior,
        behavior.buttons[WagerType.FIELD].center,
    )

    assert behavior.take_down(WagerType.FIELD)
    assert not behavior.take_down(WagerType.HOP)

    click(
        behavior,
        behavior.buttons[WagerType.FIELD].center,
    )

    assert not behavior.take_down(WagerType.FIELD)


def test_preferences_applied_to_new_game(ui_app):
    from ui.states.title_state import TitleState

    ui_app.states.reset(TitleState(ui_app))

    setup, behavior = open_behavior(ui_app)

    click(
        behavior,
        behavior.buttons[WagerType.HOP].center,
    )

    click(behavior, behavior.BACK_BUTTON.center)

    assert ui_app.states.current is setup

    setup.start_game()

    assert ui_app.wager_preferences.take_down_on_win[
        WagerType.HOP
    ]


def test_cancel_setup_preserves_preferences(ui_app):
    from ui.states.title_state import TitleState

    ui_app.states.reset(TitleState(ui_app))

    setup, behavior = open_behavior(ui_app)

    click(
        behavior,
        behavior.buttons[WagerType.FIELD].center,
    )

    assert behavior.take_down(WagerType.FIELD)

    # Preferences are only pending.
    assert not ui_app.wager_preferences.take_down_on_win.get(
        WagerType.FIELD,
        False,
    )

    click(behavior, behavior.BACK_BUTTON.center)
    setup.go_back()

    # Canceling setup must not change the app.
    assert not ui_app.wager_preferences.take_down_on_win.get(
        WagerType.FIELD,
        False,
    )
