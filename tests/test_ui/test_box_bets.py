
import pytest

from engine import WagerType
from ui.animations import AnimationMode

from .helpers import click, select_chip, run_until_idle


@pytest.mark.parametrize(
    "ui_app",
    list(AnimationMode),
    indirect=True,
)
@pytest.mark.parametrize("number", [4, 5, 6, 8, 9, 10])
@pytest.mark.parametrize(
    "name,wager_type",
    [
        ("PLACE", WagerType.PLACE_BET),
        ("LAY", WagerType.LAY_BET),
    ],
)
def test_box_bet_placement(
    ui_app,
    number,
    name,
    wager_type,
):
    state = ui_app.states.current

    area = state.get_betting_area(f"{name} {number}")

    select_chip(state, 25)
    click(state, area.rect.center)
    run_until_idle(state)

    wager = state.engine.get_wager(
        state.player,
        wager_type,
        target=number,
    )

    assert wager is not None
    assert wager.value == 25
    assert wager in state.wager_sprites

    assert state.wager_sprites[
        wager
    ].rect.center == pytest.approx(
        area.rect.center,
        abs=1,
    )
