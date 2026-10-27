
from engine import WagerType

from .helpers import (
    click,
    select_chip,
    run_until_idle,
    force_roll,
)


def test_ats_progress_display(ui_app):
    state = ui_app.states.current
    sprite = state.bonus_progress_sprite

    select_chip(state, 5)
    click(
        state,
        state.get_betting_area("ATS SMALL").rect.center,
    )
    run_until_idle(state)

    force_roll(state, 2)
    force_roll(state, 4)

    ats_hits, fire_hits, active_ats, fire_active = (
        sprite.progress()
    )

    assert ats_hits == {2, 4}
    assert WagerType.ATS_SMALL in active_ats
    assert not fire_active

    force_roll(state, 7)

    assert sprite.progress()[0] == frozenset()
    assert sprite.progress()[2] == frozenset()


def test_fire_progress_display(ui_app):
    state = ui_app.states.current
    sprite = state.bonus_progress_sprite

    select_chip(state, 5)
    click(
        state,
        state.get_betting_area("FIRE").rect.center,
    )
    run_until_idle(state)

    for number in (4, 6):
        force_roll(state, number)
        force_roll(state, number)

    ats_hits, fire_hits, active_ats, fire_active = (
        sprite.progress()
    )

    assert fire_hits == {4, 6}
    assert fire_active
    assert not active_ats

    force_roll(state, 8)
    force_roll(state, 7)

    assert sprite.progress()[1] == frozenset()
    assert not sprite.progress()[3]
