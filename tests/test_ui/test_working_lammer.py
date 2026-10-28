
import pytest

from engine import Wager, WagerType, defs

from ui.game_elements.working_lammer import (
    lammer_label,
)


@pytest.fixture
def make_wager(ui_app):
    game = ui_app.engine
    player = game.players[0]

    def create(definition, target=None):
        return Wager(
            definition=definition,
            player=player,
            game=game,
            value=25,
            target=target,
        )

    return create


@pytest.mark.parametrize(
    "working,point,expected",
    [
        (False, None, None),
        (True, None, "ON"),
        (True, 6, None),
        (False, 6, "OFF"),
    ],
)
def test_place_lammer(
    make_wager,
    working,
    point,
    expected,
):
    wager = make_wager(defs.PLACE_BET, target=6)
    wager.is_working = working

    assert lammer_label(wager, point) == expected


@pytest.mark.parametrize(
    "working,point,expected",
    [
        (False, None, None),
        (True, None, "ON"),
        (True, 8, None),
        (False, 8, "OFF"),
    ],
)
def test_hardway_lammer(
    make_wager,
    working,
    point,
    expected,
):
    wager = make_wager(defs.HARDWAY, target=8)
    wager.is_working = working

    assert lammer_label(wager, point) == expected


def test_field_never_shows_lammer(make_wager):
    wager = make_wager(defs.FIELD)

    assert lammer_label(wager, None) is None
    assert lammer_label(wager, 6) is None
