import pytest
from collections.abc import Sequence

from craps_engine.game import Game
from craps_engine.player import Player
from craps_engine.wager import Wager, WagerDefinition, WagerResult
from craps_engine.enums import WagerType
from craps_engine import wager_rules as rules



@pytest.fixture
def game_setup() -> tuple[Game, Player]:
    game = Game()
    player = game.add_player()
    return game, player


@pytest.fixture
def game(game_setup) -> Game:
    game, _ = game_setup
    return game


@pytest.fixture
def player(game_setup) -> Player:
    _, player = game_setup
    return player

@pytest.fixture
def dummy_wager(game_setup) -> tuple[Game, Player, Wager]:
    game, player = game_setup

    dummy_def = WagerDefinition(
        wager_type=WagerType.TEST_WAGER,
        name="Test Wager",
        resolution_rule=rules.simple_resolution(
            winning_totals={2,4,6,8,10,12},
        ),
        placement_rule=rules.validate_no_duplicates,
        payout_rule=rules.even_money_payout,
    )

    wager = Wager(
        definition=dummy_def,
        game=game,
        player=player,
        value=25,
    )

    game.place_wager(wager)

    return game, player, wager


def get_result(
    results: list[WagerResult],
    wager: Wager,
) -> WagerResult:
    return next(
        result for result in results
        if result.wager is wager
    )

def result_for(
        results: Sequence[WagerResult], 
        wager: Wager,
    ) -> WagerResult:
    matches = [
        result for result in results
        if result.wager is wager
    ]

    assert len(matches) == 1, (
        f"Expected exactly one result for {wager}; "
        f"found {len(matches)}."
    )

    return matches[0]