from engine import Wager, WagerType, defs
from ui.settings import WagerPreferences


def test_default_is_stay_up(ui_app):
    preferences = ui_app.wager_preferences
    game = ui_app.engine
    player = game.players[0]

    wager = Wager(
        definition=defs.FIELD,
        player=player,
        game=game,
        value=25,
    )

    assert not preferences.should_take_down(wager)


def test_type_override(ui_app):
    preferences = ui_app.wager_preferences
    preferences.take_down_on_win[WagerType.FIELD] = True

    game = ui_app.engine
    player = game.players[0]

    field = Wager(
        definition=defs.FIELD,
        player=player,
        game=game,
        value=25,
    )

    proposition = Wager(
        definition=defs.ANY_SEVEN,
        player=player,
        game=game,
        value=25,
    )

    assert preferences.should_take_down(field)
    assert not preferences.should_take_down(proposition)


def test_preferences_survive_new_game(ui_app):
    preferences = ui_app.wager_preferences

    preferences.take_down_on_win[WagerType.HOP] = True

    ui_app.new_game()

    assert ui_app.wager_preferences is preferences
    assert ui_app.wager_preferences.take_down_on_win[
        WagerType.HOP
    ]

def test_contract_wagers_cannot_auto_take_down(ui_app):
    preferences = ui_app.wager_preferences

    preferences.take_down_on_win[
        WagerType.PASS_LINE
    ] = True

    game = ui_app.engine
    player = game.players[0]

    wager = Wager(
        definition=defs.PASS_LINE,
        player=player,
        game=game,
        value=25,
    )

    assert not preferences.should_take_down(wager)