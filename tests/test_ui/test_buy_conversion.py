
import pytest

from engine import GameSettings, VigSetting, WagerType
from ui.animations import AnimationMode
from ui.input import CursorTool

from .helpers import click, select_chip, run_until_idle



@pytest.mark.parametrize(
    "ui_app_upfront",
    list(AnimationMode),
    indirect=True,
)
def test_buy_place_conversion(ui_app_upfront):
    state = ui_app_upfront.states.current

    state.app.working_preferences.place_on_comeout = True

    select_chip(state, 100)
    click(
        state,
        state.get_betting_area("PLACE 4").rect.center,
    )
    run_until_idle(state)

    wager = state.engine.get_wager(
        state.player,
        WagerType.PLACE_BET,
        target=4,
    )

    assert wager is not None

    original_id = wager.id

    assert wager.is_buy is False
    assert wager.collected_vig == 0
    assert state.player.bankroll == 1400

    # Convert Place to Buy.
    click(
        state,
        state.tool_buttons[CursorTool.BUY].center,
    )
    click(state, state.wager_sprites[wager].rect.center)
    state.update(1 / 60)

    assert wager.is_buy is True
    assert wager.collected_vig == 5
    assert state.player.bankroll == 1395
    assert state.wager_sprites[wager].color == (160, 105, 35)

    # Convert Buy back to Place.
    click(
        state,
        state.tool_buttons[CursorTool.PLACE].center,
    )
    click(state, state.wager_sprites[wager].rect.center)
    state.update(1 / 60)

    assert wager.is_buy is False
    assert wager.collected_vig == 0
    assert state.player.bankroll == 1400
    assert state.wager_sprites[wager].color == (35, 74, 180)

    # Same wager throughout conversion.
    assert wager.id == original_id
    assert wager.value == 100
    assert wager in state.engine.wagers
    assert wager in state.wager_sprites
    assert state.player_sprite.displayed_bankroll == 1400



@pytest.mark.parametrize(
    "ui_app",
    list(AnimationMode),
    indirect=True,
)
def test_auto_buy_and_threshold(ui_app):
    state = ui_app.states.current

    # Keep Place/Buy wagers working during comeout.
    # This test is concerned with AUTO_BUY behavior,
    # not automatic working-status transitions.
    state.app.working_preferences.place_on_comeout = True

    assert (
        state.engine.settings.buy_vig_setting
        is VigSetting.AUTO_BUY
    )

    # $25 Place 4 qualifies for AUTO_BUY.
    select_chip(state, 25)
    click(
        state,
        state.get_betting_area("PLACE 4").rect.center,
    )
    run_until_idle(state)

    wager = state.engine.get_wager(
        state.player,
        WagerType.PLACE_BET,
        target=4,
    )

    assert wager is not None
    assert wager._is_buy is False
    assert wager.is_buy is True

    sprite = state.wager_sprites[wager]

    state.update(1 / 60)
    assert sprite.color == (160, 105, 35)

    # PLACE cannot override automatic buying.
    click(
        state,
        state.tool_buttons[CursorTool.PLACE].center,
    )
    click(state, sprite.rect.center)
    state.update(1 / 60)

    assert wager._is_buy is False
    assert wager.is_buy is True
    assert sprite.color == (160, 105, 35)

    # Lower $25 wager to $15.
    select_chip(state, 10)
    click(state, sprite.rect.center, button=3)
    run_until_idle(state)
    state.update(1 / 60)

    assert wager.value == 15
    assert wager._is_buy is False
    assert wager.is_buy is False
    assert sprite.color == (35, 74, 180)

    # Raise to $25 again.
    click(state, sprite.rect.center)
    run_until_idle(state)
    state.update(1 / 60)

    assert wager.value == 25
    assert wager.is_buy is True
    assert sprite.color == (160, 105, 35)

    # No upfront commission under AUTO_BUY.
    assert wager.collected_vig == 0
    assert state.player.bankroll == 1475
