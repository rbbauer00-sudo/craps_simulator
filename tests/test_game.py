import pytest

from craps_engine import wager_definitions as defs
from craps_engine import constants as const
from craps_engine.game import Game
from craps_engine.wager import Wager
from craps_engine.player import Player
from craps_engine.dice import RollResult
from craps_engine.exceptions import GameRuleViolation
from craps_engine.enums import WagerType


def test_player_game_creation(game_setup):
    game, player = game_setup
    assert isinstance(game, Game)
    assert isinstance(player, Player)
    assert player.name == "Player 0"

@pytest.mark.parametrize(
    "point",
    const.BOX_NUMS,
)
@pytest.mark.parametrize(
    "roll",
    const.ALL_NUMS,
)
def test_point_update(
    game,
    point,
    roll,
):
    game._point = None
    
    game._update_point(
        RollResult(point)
    )
    
    assert game.point == point

    if roll not in (point, 7):
        game._update_point(
            RollResult(roll)
        )
        assert game.point == point

    game._update_point(
        RollResult(point)
    )
    
    assert game.point is None
    
    game._point = point
    
    game._update_point(
        RollResult(7)
    )
    assert game.point is None


@pytest.mark.parametrize(
        "func_name, kwargs",
        [
            ("increase_wager", {"amount": 10}),
            ("decrease_wager", {"amount": 10}),
            ("take_down_wager", {}),
        ],
)
def test_inactive_wagers_raise_error(
    game_setup,
    func_name,
    kwargs,
):
    game, player = game_setup


    wager = Wager(
        definition=defs.PASS_LINE,
        player=player,
        game=game,
        value=10,
    )


    func = getattr(game, func_name)

    with pytest.raises(GameRuleViolation):
        func(wager, **kwargs)
   
   
def test_increase_wager(dummy_wager):
    game, _, wager = dummy_wager

    game.increase_wager(wager, 10)

    assert wager.value == 35


def test_decrease_wager(dummy_wager):
    game, _, wager = dummy_wager

    game.decrease_wager(wager, 10)

    assert wager.value == 15


def test_take_down_wager(dummy_wager):
    game, _, wager = dummy_wager

    game.take_down_wager(wager)

    assert wager not in game.wagers


def test_get_wager(dummy_wager):
    game, player, wager = dummy_wager

    gotten_wager = game.get_wager(
        player=player,
        wager_type=WagerType.TEST_WAGER,
    )

    assert gotten_wager is wager


@pytest.mark.parametrize(
    "definition",
    [
        defs.FIELD,
        defs.COME,
        defs.DONT_COME,
        defs.PASS_LINE,
        defs.DONT_PASS,
    ],
)
def test_wager_cannot_be_turned_off(game_setup, definition):
    game, player = game_setup

    wager = Wager(
        definition=definition,
        player=player,
        game=game,
        value=25,
    )

    assert wager.is_working is True
    assert wager.definition.can_turn_off is False

    with pytest.raises(GameRuleViolation):
        wager.is_working = False

    assert wager.is_working is True

