
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
def come_game(ui_app):
    state = ui_app.states.current

    # Establish a table point of 4.
    force_roll(state, 4)
    assert state.engine.point == 4

    # Place a $25 Come bet.
    select_chip(state, 25)
    click(
        state,
        state.get_betting_area("COME").rect.center,
    )
    run_until_idle(state)

    wager = state.engine.get_wager(
        state.player,
        WagerType.COME,
    )

    assert wager is not None
    assert wager.target is None

    return state, wager


def test_come_bet_travels(come_game):
    state, wager = come_game

    original_sprite = state.wager_sprites[wager]

    # Roll a 6 to establish the Come point.
    force_roll(state, 6)

    assert wager.target == 6
    assert wager in state.engine.wagers
    assert wager in state.wager_sprites

    # The original chip should be moved,
    # not replaced with a new wager sprite.
    sprite = state.wager_sprites[wager]

    assert sprite is original_sprite
    assert sprite.rect.center == pytest.approx(
        state.COME_POSITIONS[6],
        abs=1,
    )

    # No win or loss yet.
    assert state.player.bankroll == 1475


def test_traveled_come_bet_wins(come_game):
    state, wager = come_game

    force_roll(state, 6)
    assert wager.target == 6

    # The Come bet wins when 6 repeats.
    force_roll(state, 6)

    assert wager not in state.engine.wagers
    assert wager not in state.wager_sprites

    # $25 stake returned + $25 profit.
    assert state.player.bankroll == 1525
    assert state.player_sprite.displayed_bankroll == 1525


def test_traveled_come_bet_loses_on_seven(come_game):
    state, wager = come_game

    force_roll(state, 6)
    assert wager.target == 6

    # A seven-out loses the traveled Come bet.
    force_roll(state, 7)

    assert state.engine.point is None
    assert wager not in state.engine.wagers
    assert wager not in state.wager_sprites

    # Original $25 wager is lost.
    assert state.player.bankroll == 1475
    assert state.player_sprite.displayed_bankroll == 1475


def place_come_bet(state, amount=25):
    select_chip(state, amount)

    click(
        state,
        state.get_betting_area("COME").rect.center,
    )
    run_until_idle(state)

    wager = state.engine.get_wager(
        state.player,
        WagerType.COME,
        target=None,
    )

    assert wager is not None
    assert wager.value == amount

    return wager


def test_three_point_molly_all_lose(come_game):
    state, first_wager = come_game

    # First Come bet travels to 5.
    force_roll(state, 5)
    assert first_wager.target == 5

    # Second Come bet travels to 6.
    second_wager = place_come_bet(state)
    force_roll(state, 6)
    assert second_wager.target == 6

    # Third Come bet travels to 8.
    third_wager = place_come_bet(state)
    force_roll(state, 8)
    assert third_wager.target == 8

    wagers = (
        first_wager,
        second_wager,
        third_wager,
    )

    # All three wagers are still active.
    assert all(
        wager in state.engine.wagers
        for wager in wagers
    )

    assert len(set(wagers)) == 3
    assert state.player.bankroll == 1425

    # Verify all three chip positions.
    for wager in wagers:
        sprite = state.wager_sprites[wager]

        assert sprite.rect.center == pytest.approx(
            state.COME_POSITIONS[wager.target],
            abs=1,
        )

    # Seven-out loses all three Come bets.
    force_roll(state, 7)

    assert state.engine.point is None

    for wager in wagers:
        assert wager not in state.engine.wagers
        assert wager not in state.wager_sprites

    assert state.player.bankroll == 1425
    assert state.player_sprite.displayed_bankroll == 1425


def test_three_point_molly_independent_resolution(come_game):
    state, first_wager = come_game

    force_roll(state, 5)

    second_wager = place_come_bet(state)
    force_roll(state, 6)

    third_wager = place_come_bet(state)
    force_roll(state, 8)

    # The table point is still 4.
    assert state.engine.point == 4

    # Roll 5: first Come bet wins.
    force_roll(state, 5)

    assert first_wager not in state.engine.wagers
    assert first_wager not in state.wager_sprites

    # Other Come bets must remain active.
    for wager in (second_wager, third_wager):
        assert wager in state.engine.wagers
        assert wager in state.wager_sprites

    # Three $25 bets initially cost $75.
    # First win returns $50.
    assert state.player.bankroll == 1475

    # Seven-out loses the remaining Come bets.
    force_roll(state, 7)

    assert state.engine.point is None

    for wager in (second_wager, third_wager):
        assert wager not in state.engine.wagers
        assert wager not in state.wager_sprites

    assert state.player.bankroll == 1475
    assert state.player_sprite.displayed_bankroll == 1475



def test_come_odds_betting_area(come_game):
    state, come_wager = come_game

    # Travel Come bet to 6.
    force_roll(state, 6)

    # Find its dedicated odds area.
    odds_area = next(
        area for area in state.areas
        if area.name == "COME 6 ODDS"
    )

    select_chip(state, 25)
    click(state, odds_area.rect.center)
    run_until_idle(state)

    odds = state.engine.get_child_wager(come_wager)

    assert odds is not None
    assert odds.parent_wager is come_wager
    assert odds.value == 25
    assert odds.target == 6

    assert odds in state.wager_sprites

    # Win both Come and odds.
    force_roll(state, 6)

    assert come_wager not in state.engine.wagers
    assert odds not in state.engine.wagers

    assert come_wager not in state.wager_sprites
    assert odds not in state.wager_sprites

    assert state.player.bankroll == 1555
    assert state.player_sprite.displayed_bankroll == 1555
