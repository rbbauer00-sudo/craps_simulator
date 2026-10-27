
from engine import VigSetting
from ui.craps_app import CrapsApp
from ui.states.new_game_state import NewGameState
from ui.states.table_rules_state import TableRulesState

import pygame as pg


def test_rules_are_applied_to_new_game():
    app = CrapsApp(start_on_title=True)

    try:
        app.states.current.start_game()
        setup = app.states.current

        assert isinstance(setup, NewGameState)

        rules = TableRulesState(app, setup)

        rules.change_rule("BUY VIG", 1)
        rules.change_rule("AUTO BUY LEVEL", 1)
        rules.change_rule("FIELD 12", 1)
        rules.change_rule("PUT BETS", 1)

        assert (
            setup.game_settings.buy_vig_setting
            is VigSetting.ON_WIN
        )
        assert setup.game_settings.auto_buy_level == 25
        assert not setup.game_settings.field_3x_on_12
        assert not setup.game_settings.allow_put_bets

        setup.start_game()

        settings = app.engine.settings

        assert settings == setup.game_settings

    finally:
        pg.quit()


def test_rules_screen_returns_to_setup():
    app = CrapsApp(start_on_title=True)

    try:
        app.states.current.start_game()
        setup = app.states.current

        app.states.push(
            TableRulesState(app, setup)
        )

        rules = app.states.current

        assert isinstance(rules, TableRulesState)

        rules.change_rule("FIELD 12", 1)
        rules.app.states.pop()

        assert app.states.current is setup
        assert not setup.game_settings.field_3x_on_12

    finally:
        pg.quit()
