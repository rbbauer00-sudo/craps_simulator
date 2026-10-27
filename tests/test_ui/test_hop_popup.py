
import pygame as pg
import pytest

from engine import WagerType
from engine.constants import HOP_TARGETS
from ui.animations import AnimationMode
from ui.states.hop_bet_state import HopBetState

from .helpers import click, force_roll, run_until_idle


pytestmark = pytest.mark.parametrize(
    "ui_app",
    list(AnimationMode),
    indirect=True,
)


def open_hops(ui_app):
    playing = ui_app.states.current

    click(playing, playing.hop_tray.RECT.center)

    popup = ui_app.states.current
    assert isinstance(popup, HopBetState)

    return playing, popup


def test_hop_popup_all_combinations(ui_app):
    playing, popup = open_hops(ui_app)

    assert set(popup.buttons) == HOP_TARGETS
    assert len(popup.buttons) == 17

    # Draw the full state stack.
    ui_app.states.draw(ui_app.screen)

    # Close with Escape.
    popup.handle_event(
        pg.event.Event(
            pg.KEYDOWN,
            {"key": pg.K_ESCAPE},
        )
    )

    assert ui_app.states.current is playing


def test_hop_popup_chip_selector(ui_app):
    playing, popup = open_hops(ui_app)

    click(popup, playing.chip_buttons[5].center)

    assert playing.selected_chip == 5
    assert ui_app.states.current is popup

    click(popup, popup.buttons[(3, 4)].center)
    run_until_idle(playing)

    wager = playing.engine.get_wager(
        playing.player,
        WagerType.HOP,
        target=(3, 4),
    )

    assert wager is not None
    assert wager.value == 5
    assert playing.player.bankroll == 1495


def test_multiple_hops_and_resolution(ui_app):
    playing, popup = open_hops(ui_app)

    click(popup, playing.chip_buttons[5].center)

    for target in ((2, 2), (3, 4), (4, 6)):
        click(popup, popup.buttons[target].center)
        run_until_idle(playing)

    assert len(playing.hop_tray.active_wagers()) == 3
    assert playing.player.bankroll == 1485

    popup.close()

    assert ui_app.states.current is playing

    # Roll 7 as 3+4: that Hop wins at 15:1.
    for char in "3,4":
        playing.forced_roll_buffer.add(char)

    playing.roll()
    run_until_idle(playing)

    winner = playing.engine.get_wager(
        playing.player,
        WagerType.HOP,
        target=(3, 4),
    )

    assert winner is not None
    assert winner in playing.wager_sprites

    assert len(playing.hop_tray.active_wagers()) == 1
    assert playing.player.bankroll == 1560


def test_hard_hop_payout(ui_app):
    playing, popup = open_hops(ui_app)

    click(popup, playing.chip_buttons[5].center)
    click(popup, popup.buttons[(3, 3)].center)
    run_until_idle(playing)

    popup.close()

    for char in "3,3":
        playing.forced_roll_buffer.add(char)

    playing.roll()
    run_until_idle(playing)

    # $5 hard hop pays 30:1 in this engine.
    assert playing.player.bankroll == 1645

    assert len(playing.hop_tray.active_wagers()) == 1
