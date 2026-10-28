
from engine import WagerType
from ui.animations import AnimationMode, AnimationSettings
from ui.states.settings_state import SettingsState
from ui.states.player_preferences_state import PlayerPreferencesState
from ui.states.wager_behavior_state import WagerBehaviorState

from .helpers import click


def open_behavior(ui_app, playing=None):
    settings = SettingsState(ui_app, playing)
    ui_app.states.push(settings)

    click(
        settings,
        settings.PLAYER_PREFERENCES_BUTTON.center,
    )

    preferences = ui_app.states.current
    assert isinstance(preferences, PlayerPreferencesState)

    click(
        preferences,
        preferences.WAGER_BEHAVIOR_BUTTON.center,
    )

    behavior = ui_app.states.current
    assert isinstance(behavior, WagerBehaviorState)

    return settings, preferences, behavior


def test_default_stay_up(ui_app):
    _, _, behavior = open_behavior(ui_app)

    for wager_type, _ in behavior.WAGER_TYPES:
        assert not behavior.take_down(wager_type)


def test_toggle_wager_behavior(ui_app):
    _, _, behavior = open_behavior(ui_app)

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


def test_preferences_apply_immediately(ui_app):
    _, _, behavior = open_behavior(ui_app)

    click(
        behavior,
        behavior.buttons[WagerType.HOP].center,
    )

    assert ui_app.wager_preferences.take_down_on_win[
        WagerType.HOP
    ]


def test_preferences_survive_new_game(ui_app):
    _, _, behavior = open_behavior(ui_app)

    click(
        behavior,
        behavior.buttons[WagerType.FIELD].center,
    )

    preferences = ui_app.wager_preferences

    ui_app.new_game()

    assert ui_app.wager_preferences is preferences
    assert preferences.take_down_on_win[WagerType.FIELD]


def test_back_navigation_preserves_preferences(ui_app):
    playing = ui_app.states.current

    settings, preferences, behavior = open_behavior(
        ui_app,
        playing,
    )

    click(
        behavior,
        behavior.buttons[WagerType.FIELD].center,
    )

    click(behavior, behavior.BACK_BUTTON.center)
    assert ui_app.states.current is preferences

    click(preferences, preferences.BACK_BUTTON.center)
    assert ui_app.states.current is settings

    click(settings, settings.BACK_BUTTON.center)
    assert ui_app.states.current is playing

    assert ui_app.wager_preferences.take_down_on_win[
        WagerType.FIELD
    ]


def test_behavior_disabled_during_animation(ui_app):
    playing = ui_app.states.current

    ui_app.set_animation_settings(
        AnimationSettings(mode=AnimationMode.FULL),
        playing_state=playing,
    )

    playing.roll()
    assert playing.is_animating

    _, _, behavior = open_behavior(ui_app, playing)

    assert not behavior.can_change_behavior

    click(
        behavior,
        behavior.buttons[WagerType.FIELD].center,
    )

    assert not behavior.take_down(WagerType.FIELD)
    assert not ui_app.wager_preferences.take_down_on_win.get(
        WagerType.FIELD,
        False,
    )
