
import pytest

from engine import WagerType, defs
from ui.animations import AnimationMode

from .helpers import run_until_idle


MODES = list(AnimationMode)


@pytest.fixture(params=MODES)
def playing(request, ui_app):
    state = ui_app.states.current

    ui_app.set_animation_settings(
        ui_app.animation_settings.__class__(
            mode=request.param,
        ),
        playing_state=state,
    )

    return state


def place_wager(
    playing,
    definition,
    *,
    target=None,
    amount=25,
    position=(500, 300),
):
    playing.change_wager(
        amount,
        definition=definition,
        target=target,
        position=position,
    )

    run_until_idle(playing)

    return next(
        wager
        for wager in playing.engine.wagers
        if wager.definition is definition
        and wager.target == target
    )


def roll_dice(playing, d1, d2):
    playing.forced_roll_buffer.add(str(d1))
    playing.forced_roll_buffer.add(",")
    playing.forced_roll_buffer.add(str(d2))

    playing.roll()
    run_until_idle(playing)


def test_field_win_stays_up(playing):
    wager = place_wager(
        playing,
        defs.FIELD,
    )

    bankroll_before = playing.player.bankroll

    roll_dice(playing, 1, 2)

    assert wager in playing.engine.wagers
    assert wager.value == 25

    # Field 3 pays even money.
    assert playing.player.bankroll == (
        bankroll_before + 25
    )

    assert wager in playing.wager_sprites
    assert playing.wager_sprites[wager].alive()


def test_field_loss_removes_wager(playing):
    wager = place_wager(
        playing,
        defs.FIELD,
    )

    bankroll_before = playing.player.bankroll

    roll_dice(playing, 3, 3)

    assert wager not in playing.engine.wagers
    assert wager not in playing.wager_sprites

    # Stake was withdrawn at placement,
    # not again when the wager lost.
    assert playing.player.bankroll == bankroll_before


def test_hop_win_and_other_hop_loss(playing):
    winning_target = (2, 3)
    losing_target = (1, 3)

    winner = place_wager(
        playing,
        defs.HOP_BET,
        target=winning_target,
        position=playing.hop_tray.position_for(
            winning_target
        ),
    )

    loser = place_wager(
        playing,
        defs.HOP_BET,
        target=losing_target,
        position=playing.hop_tray.position_for(
            losing_target
        ),
    )

    bankroll_before = playing.player.bankroll

    roll_dice(playing, 2, 3)

    assert winner in playing.engine.wagers
    assert loser not in playing.engine.wagers

    assert winner in playing.wager_sprites
    assert loser not in playing.wager_sprites

    # Easy Hop pays 15:1.
    assert playing.player.bankroll == (
        bankroll_before + 25 * 15
    )

    assert len(
        playing.hop_tray.active_wagers()
    ) == 1


def test_proposition_win_stays_up(playing):
    wager = place_wager(
        playing,
        defs.ANY_SEVEN,
    )

    bankroll_before = playing.player.bankroll

    roll_dice(playing, 3, 4)

    assert wager in playing.engine.wagers
    assert wager in playing.wager_sprites

    # Any Seven pays 4:1.
    assert playing.player.bankroll == (
        bankroll_before + 25 * 4
    )


def test_proposition_loss_removes_wager(playing):
    wager = place_wager(
        playing,
        defs.ANY_SEVEN,
    )

    bankroll_before = playing.player.bankroll

    roll_dice(playing, 3, 3)

    assert wager not in playing.engine.wagers
    assert wager not in playing.wager_sprites
    assert playing.player.bankroll == bankroll_before
