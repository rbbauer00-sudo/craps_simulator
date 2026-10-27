
import pytest

from engine import WagerType
from ui.animations import AnimationMode

from .helpers import (
    click,
    select_chip,
    run_until_idle,
    force_roll,
)


pytestmark = pytest.mark.parametrize(
    "ui_app",
    list(AnimationMode),
    indirect=True,
)


@pytest.fixture
def dp_game(ui_app):
    state = ui_app.states.current

    # Place $25 Don't Pass.
    select_chip(state, 25)

    click(
        state,
        state.get_betting_area("DON'T PASS").rect.center,
    )
    run_until_idle(state)

    parent = state.engine.get_wager(
        state.player,
        WagerType.DONT_PASS,
    )

    assert parent is not None

    # Establish point 4.
    force_roll(state, 4)

    assert state.engine.point == 4

    odds_area = next(
        area for area in state.areas
        if area.name == "DP ODDS"
    )

    return state, parent, odds_area


def place_dp_odds(state, parent, odds_area, amount=25):
    select_chip(state, amount)
    click(state, odds_area.rect.center)
    run_until_idle(state)

    odds = state.engine.get_child_wager(parent)

    assert odds is not None
    assert odds.value == amount
    assert odds.parent_wager is parent
    assert odds.target == state.engine.point

    return odds


def test_dp_odds_requires_point(ui_app):
    state = ui_app.states.current

    select_chip(state, 25)

    click(
        state,
        state.get_betting_area("DON'T PASS").rect.center
    )
    run_until_idle(state)

    parent = state.engine.get_wager(
        state.player,
        WagerType.DONT_PASS,
    )

    odds_area = next(
        area for area in state.areas
        if area.name == "DP ODDS"
    )

    original_bankroll = state.player.bankroll

    # No point exists yet.
    click(state, odds_area.rect.center)

    assert state.engine.get_child_wager(parent) is None
    assert state.player.bankroll == original_bankroll


def test_dp_odds_place_adjust_remove(dp_game):
    state, parent, odds_area = dp_game

    odds = place_dp_odds(
        state, parent, odds_area, amount=25
    )

    assert odds in state.engine.wagers
    assert odds in state.wager_sprites
    assert odds.collected_vig == 0

    # Increase by $5.
    select_chip(state, 5)

    click(
        state,
        state.wager_sprites[odds].rect.center,
    )
    run_until_idle(state)

    assert odds.value == 30

    # Decrease by $5.
    click(
        state,
        state.wager_sprites[odds].rect.center,
        button=3,
    )
    run_until_idle(state)

    assert odds.value == 25

    # Remove the odds without removing Don't Pass.
    select_chip(state, 100)

    click(
        state,
        state.wager_sprites[odds].rect.center,
        button=3,
    )
    run_until_idle(state)

    assert odds not in state.engine.wagers
    assert odds not in state.wager_sprites

    assert parent in state.engine.wagers
    assert parent in state.wager_sprites

    # Only the original Don't Pass stake remains.
    assert state.player.bankroll == 1475


def test_dp_odds_win_on_seven(dp_game):
    state, parent, odds_area = dp_game

    odds = place_dp_odds(
        state, parent, odds_area, amount=25
    )

    # Seven-out: Don't Pass and lay odds win.
    force_roll(state, 7)

    assert state.engine.point is None

    # The odds have resolved and disappeared.
    assert odds not in state.engine.wagers
    assert odds not in state.wager_sprites

    # Parent remains for the next come-out.
    assert parent in state.engine.wagers
    assert parent in state.wager_sprites

    # $1500 - $25 DP - $25 odds
    # + $25 DP profit + $25 odds stake + $12 odds profit.
    assert state.player.bankroll == 1512
    assert state.player_sprite.displayed_bankroll == 1512


def test_dp_odds_lose_on_point(dp_game):
    state, parent, odds_area = dp_game

    odds = place_dp_odds(
        state, parent, odds_area, amount=25
    )

    # Point 4 repeats: Don't Pass and odds lose.
    force_roll(state, 4)

    assert state.engine.point is None

    assert parent not in state.engine.wagers
    assert parent not in state.wager_sprites

    assert odds not in state.engine.wagers
    assert odds not in state.wager_sprites

    assert state.player.bankroll == 1450
    assert state.player_sprite.displayed_bankroll == 1450
