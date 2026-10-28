
import pytest

from engine import WagerType, defs
from ui.animations import AnimationMode

from .helpers import run_until_idle


@pytest.fixture(params=list(AnimationMode))
def playing(request, ui_app):
    state = ui_app.states.current

    ui_app.set_animation_settings(
        ui_app.animation_settings.__class__(
            mode=request.param,
        ),
        playing_state=state,
    )

    return state


def place_six(playing):
    playing.change_wager(
        30,
        definition=defs.PLACE_BET,
        target=6,
        position=playing.get_betting_area(
            "PLACE 6"
        ).rect.center,
    )

    run_until_idle(playing)

    return playing.engine.get_wager(
        playing.player,
        WagerType.PLACE_BET,
        target=6,
    )


def roll(playing, dice):
    for char in dice:
        playing.forced_roll_buffer.add(char)

    playing.roll()
    run_until_idle(playing)


def test_place_bet_off_on_comeout(playing):
    wager = place_six(playing)

    assert playing.engine.point is None
    assert not wager.is_working


def test_place_bet_on_after_point_established(playing):
    wager = place_six(playing)

    # Establish point 5.
    roll(playing, "2,3")

    assert playing.engine.point == 5
    assert wager.is_working


def test_place_bet_off_after_point_made(playing):
    wager = place_six(playing)

    roll(playing, "2,3")
    assert wager.is_working

    # Make point 5.
    roll(playing, "2,3")

    assert playing.engine.point is None
    assert not wager.is_working


def test_manual_override_survives_point_change(playing):
    wager = place_six(playing)

    # Establish point 5.
    roll(playing, "2,3")

    assert wager.is_working

    # Manually turn wager off.
    playing.set_manual_working_status(wager)

    assert not wager.is_working
    assert wager in playing.manual_working_overrides

    # Make point 5.
    roll(playing, "2,3")

    assert playing.engine.point is None
    assert not wager.is_working

    # Establish new point 4.
    roll(playing, "1,3")

    assert playing.engine.point == 4

    # Manual OFF remains in effect.
    assert not wager.is_working


def test_manual_on_during_comeout(playing):
    wager = place_six(playing)

    assert not wager.is_working

    playing.set_manual_working_status(wager)

    assert wager.is_working

    # Establish point 5.
    roll(playing, "2,3")

    assert wager.is_working

    # Make point 5, returning to comeout.
    roll(playing, "2,3")

    assert playing.engine.point is None

    # Manual ON remains in effect.
    assert wager.is_working


def test_preferences_can_enable_place_on_comeout(
    playing,
):
    playing.app.working_preferences.place_on_comeout = True

    wager = place_six(playing)

    assert wager.is_working


def test_hardway_comeout_preference(playing):
    playing.app.working_preferences.hardway_on_comeout = False

    playing.change_wager(
        25,
        definition=defs.HARDWAY,
        target=8,
        position=playing.get_betting_area(
            "HARD 8"
        ).rect.center,
    )

    run_until_idle(playing)

    wager = playing.engine.get_wager(
        playing.player,
        WagerType.HARDWAY,
        target=8,
    )

    assert not wager.is_working

    # Establish point 5.
    roll(playing, "2,3")

    assert wager.is_working