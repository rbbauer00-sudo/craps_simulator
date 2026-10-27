
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

ATS_CASES = [
    (
        "ATS SMALL",
        WagerType.ATS_SMALL,
        (2, 3, 4, 5, 6),
        35,
    ),
    (
        "ATS TALL",
        WagerType.ATS_TALL,
        (8, 9, 10, 11, 12),
        35,
    ),
    (
        "ATS ALL",
        WagerType.ATS_ALL,
        (2, 3, 4, 5, 6, 8, 9, 10, 11, 12),
        176,
    ),
]


@pytest.mark.parametrize(
    "area_name,wager_type,rolls,multiple",
    ATS_CASES,
)
def test_ats_wins(
    ui_app,
    area_name,
    wager_type,
    rolls,
    multiple,
):
    state = ui_app.states.current

    select_chip(state, 5)
    click(
        state,
        state.get_betting_area(area_name).rect.center,
    )
    run_until_idle(state)

    wager = next(
        w for w in state.engine.wagers
        if w.definition.wager_type is wager_type
    )

    assert wager.value == 5
    assert state.player.bankroll == 1495

    for roll in rolls:
        force_roll(state, roll)

    assert wager.targets_hit == set(rolls)
    assert wager not in state.engine.wagers
    assert wager not in state.wager_sprites

    # Profit plus returned original wager.
    expected = 1500 + 5 * multiple

    assert state.player.bankroll == expected
    assert (
        state.player_sprite.displayed_bankroll
        == expected
    )


@pytest.mark.parametrize(
    "area_name,wager_type,rolls,multiple",
    ATS_CASES,
)
def test_ats_loses_on_seven(
    ui_app,
    area_name,
    wager_type,
    rolls,
    multiple,
):
    state = ui_app.states.current

    select_chip(state, 5)
    click(
        state,
        state.get_betting_area(area_name).rect.center,
    )
    run_until_idle(state)

    wager = next(
        w for w in state.engine.wagers
        if w.definition.wager_type is wager_type
    )

    # Accumulate partial progress.
    force_roll(state, rolls[0])
    force_roll(state, rolls[1])

    assert wager.targets_hit == set(rolls[:2])
    assert wager in state.engine.wagers

    force_roll(state, 7)

    assert wager not in state.engine.wagers
    assert wager not in state.wager_sprites
    assert state.player.bankroll == 1495