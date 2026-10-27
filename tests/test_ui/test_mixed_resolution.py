
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


def place_in_area(state, name, amount=25):
    select_chip(state, amount)

    area = state.get_betting_area(name)

    click(state, area.rect.center)
    run_until_idle(state)


def test_mixed_seven_out(ui_app):
    state = ui_app.states.current
    player = state.player
    engine = state.engine

    # ---------------------------------
    # Establish Don't Pass and point 4.
    # ---------------------------------

    place_in_area(state, "DON'T PASS")

    dont_pass = engine.get_wager(
        player,
        WagerType.DONT_PASS,
    )
    assert dont_pass is not None

    force_roll(state, 4)
    assert engine.point == 4

    # Add $25 lay odds.
    place_in_area(state, "DP ODDS")

    dp_odds = engine.get_child_wager(dont_pass)
    assert dp_odds is not None
    assert dp_odds.value == 25

    # ---------------------------------
    # Establish three Come bets.
    # ---------------------------------

    come_wagers = []
    come_odds = []

    for number in (5, 6, 8):

        place_in_area(state, "COME")

        come = engine.get_wager(
            player,
            WagerType.COME,
            target=None,
        )
        assert come is not None

        force_roll(state, number)

        assert come.target == number

        # Place $25 odds on that Come number.
        place_in_area(
            state,
            f"COME {number} ODDS",
        )

        odds = engine.get_child_wager(come)

        assert odds is not None
        assert odds.value == 25
        assert odds.target == number
        assert odds.parent_wager is come

        come_wagers.append(come)
        come_odds.append(odds)

    # ---------------------------------
    # Verify setup.
    # ---------------------------------

    all_wagers = (
        dont_pass,
        dp_odds,
        *come_wagers,
        *come_odds,
    )

    assert len(set(all_wagers)) == 8

    for wager in all_wagers:
        assert wager in engine.wagers
        assert wager in state.wager_sprites

    # $25 DP + $25 DP odds
    # + 3 Come bets at $25
    # + 3 Come odds at $25
    # Total committed = $200.
    assert player.bankroll == 1300

    # ---------------------------------
    # Seven-out.
    # ---------------------------------

    force_roll(state, 7)

    assert engine.point is None

    # All three Come bets and their odds lose.
    for wager in (*come_wagers, *come_odds):
        assert wager not in engine.wagers
        assert wager not in state.wager_sprites

    # Don't Pass wins and stays on the table.
    assert dont_pass in engine.wagers
    assert dont_pass in state.wager_sprites

    # Its lay odds win and are removed.
    assert dp_odds not in engine.wagers
    assert dp_odds not in state.wager_sprites

    # No orphaned wager sprites.
    assert set(state.wager_sprites) == set(engine.wagers)

    # ---------------------------------
    # Verify bankroll.
    # ---------------------------------

    # Starting bankroll:          $1500
    # Eight $25 wagers:           -$200
    # Don't Pass profit:           +$25
    # Lay odds principal returned: +$25
    # Lay odds profit (1:2):       +$12
    # Final liquid bankroll:      $1362

    assert player.bankroll == 1362
    assert state.player_sprite.displayed_bankroll == 1362

    assert not state.is_animating
    assert state.current_roll is None
