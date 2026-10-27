
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


PROP_CASES = [
    ("ANY SEVEN", WagerType.ANY_SEVEN, 7, 4),
    ("ANY CRAPS", WagerType.ANY_CRAPS, 3, 7),
    ("YO", WagerType.YO_LEVEN, 11, 15),
    ("ACE DEUCE", WagerType.ACE_DEUCE, 3, 15),
    ("DEUCE", WagerType.DEUCE, 2, 30),
    ("MIDNIGHT", WagerType.MIDNIGHT, 12, 30),
]


@pytest.mark.parametrize(
    "area_name,wager_type,winning_roll,payout",
    PROP_CASES,
)
def test_proposition_win(
    ui_app,
    area_name,
    wager_type,
    winning_roll,
    payout,
):
    state = ui_app.states.current

    select_chip(state, 25)

    click(
        state,
        state.get_betting_area(area_name).rect.center,
    )
    run_until_idle(state)

    wager = state.engine.get_wager(
        state.player,
        wager_type,
    )

    assert wager is not None
    assert wager.value == 25

    force_roll(state, winning_roll)

    # Winning wager remains active under
    # the current engine policy.
    assert wager in state.engine.wagers
    assert wager in state.wager_sprites

    assert state.player.bankroll == 1475 + 25 * payout
    assert (
        state.player_sprite.displayed_bankroll
        == state.player.bankroll
    )


@pytest.mark.parametrize(
    "area_name,wager_type,winning_roll,payout",
    PROP_CASES,
)
def test_proposition_loss(
    ui_app,
    area_name,
    wager_type,
    winning_roll,
    payout,
):
    state = ui_app.states.current

    select_chip(state, 25)

    click(
        state,
        state.get_betting_area(area_name).rect.center,
    )
    run_until_idle(state)

    wager = state.engine.get_wager(
        state.player,
        wager_type,
    )

    assert wager is not None

    # Roll 5 loses every proposition listed above.
    force_roll(state, 5)

    assert wager not in state.engine.wagers
    assert wager not in state.wager_sprites

    assert state.player.bankroll == 1475
    assert state.player_sprite.displayed_bankroll == 1475
