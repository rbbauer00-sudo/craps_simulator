import pytest

from engine import wager_definitions as defs
from engine import constants as const
from engine.game import Game
from engine.wager import Wager
from engine.player import Player
from engine.dice import RollResult
from engine.exceptions import GameRuleViolation, InsufficientFundsError
from engine.enums import WagerType


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


def test_shooter_advances_on_seven_out():
    game = Game()
    player1 = game.add_player()
    player2 = game.add_player()

    assert game.shooter is player1

    game.roll(2, 2)  # Establish point 4
    result = game.roll(1, 6)  # Seven-out

    assert result.seven_out is True
    assert result.shooter_id == player1.id
    assert result.shooter_roll_count == 2

    assert game.shooter is player2
    assert game.shooter_roll_count == 0
    assert game.point is None


def test_wager_ids_are_sequential(game_setup):
    game, player = game_setup

    wager1 = Wager(
        definition=defs.PASS_LINE,
        player=player,
        game=game,
        value=25,
    )

    game.place_wager(wager1)

    game.roll(2, 2)  # Establish point 4
    game.roll(1, 6)  # Seven-out; wager loses

    wager2 = Wager(
        definition=defs.PASS_LINE,
        player=player,
        game=game,
        value=25,
    )

    game.place_wager(wager2)

    assert wager1.id == 0
    assert wager2.id == 1
    assert game._next_wager_id == 2


def test_rejected_wager_does_not_consume_id(game_setup):
    game, player = game_setup

    wager = Wager(
        definition=defs.PASS_LINE,
        player=player,
        game=game,
        value=2000,
    )

    with pytest.raises(InsufficientFundsError):
        game.place_wager(wager)

    assert wager.id is None
    assert game._next_wager_id == 0
    assert not game.wagers


def test_wager_id_cannot_be_reused(game_setup):
    game, player = game_setup

    wager = Wager(
        definition=defs.PASS_LINE,
        player=player,
        game=game,
        value=25,
    )

    game.place_wager(wager)
    game.take_down_wager(wager)

    with pytest.raises(ValueError):
        game.place_wager(wager)

    assert wager.id == 0
    assert game._next_wager_id == 1