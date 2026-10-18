import pytest
from conftest import result_for
from typing import Protocol

from craps_engine import wager_definitions as defs
from craps_engine import constants as const
from craps_engine.game import Game
from craps_engine.player import Player
from craps_engine.wager import Wager
from craps_engine.dice import RollResult
from craps_engine.enums import Resolution, WagerType
from craps_engine.exceptions import GameRuleViolation, InsufficientFundsError


PROFIT_BY_POINT = {4: 60, 5: 45, 6: 36, 8: 36, 9: 45, 10: 60}

OddsSetup = tuple[Game, Player, Wager, Wager]


class OddsFactory(Protocol):
    def __call__(
        self,
        target: int = 6,
        parent_type: WagerType = WagerType.PASS_LINE,
        odds_value: int = 30,
    ) -> OddsSetup: ...


@pytest.fixture
def odds_game(
    game_setup: tuple[Game, Player]
) -> OddsFactory:

    game, player = game_setup

    def _setup(
        target: int = 6,
        parent_type: WagerType = WagerType.PASS_LINE,
        odds_value: int = 30,
    ) -> OddsSetup:
        assert target in const.BOX_NUMS

        if parent_type is WagerType.PASS_LINE:
            parent_def = defs.PASS_LINE
            parent = Wager(
                definition=parent_def, 
                player=player,
                game=game, 
                value=25,
            )

            game.place_wager(parent)
            game.roll(target)  # Establish the table point normally.
            assert game.point == target

        elif parent_type is WagerType.COME:
            parent_def = defs.COME
            game._point = 5 if target != 5 else 6
            parent = Wager(
                definition=parent_def, 
                player=player,
                game=game, 
                value=25,
            )

            game.place_wager(parent)
            game.roll(target)  # Move Come wager to its number.
            assert parent.target == target
            assert game.point != target

        else:
            raise ValueError(f"Unsupported parent type: {parent_type}")

        odds = Wager(
            definition=defs.LINE_ODDS,
            player=player,
            game=game,
            value=odds_value,
            parent_wager=parent,
        )

        game.place_wager(odds)
        return game, player, parent, odds

    return _setup



def test_wager_definition():
    wager_def = defs.LINE_ODDS

    assert wager_def.wager_type is WagerType.LINE_ODDS
    assert wager_def.name == "Line Odds"
    assert wager_def.can_turn_off is True
    assert wager_def.remove_after_win is True

# -----------------------------------------------------------------------------
# PLACEMENT
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("parent_type", [WagerType.PASS_LINE, WagerType.COME])
@pytest.mark.parametrize("target", const.BOX_NUMS)
def test_placement_assigns_parent_and_target(odds_game: OddsFactory, parent_type, target):
    game, player, parent, odds = odds_game(target, parent_type)
    assert odds in game.wagers
    assert odds in player.get_wagers()
    assert odds.parent_wager is parent
    assert odds.target == target
    assert game.get_child_wager(parent) is odds
    assert player.bankroll == 1500 - 25 - 30


@pytest.mark.parametrize("parent_type", [WagerType.PASS_LINE, WagerType.COME])
def test_duplicate_odds_rejected_without_charging(odds_game: OddsFactory, parent_type):
    game, player, parent, odds = odds_game(6, parent_type)
    before = player.bankroll
    duplicate = Wager(
        definition=defs.LINE_ODDS,
        player=player,
        game=game,
        value=20,
        parent_wager=parent,
    )
    with pytest.raises(GameRuleViolation):
        game.place_wager(duplicate)
    assert duplicate not in game.wagers
    assert odds in game.wagers
    assert player.bankroll == before


@pytest.mark.parametrize("value", [0, -1, -25])
def test_nonpositive_odds_rejected(odds_game: OddsFactory, value):
    game, player, parent, odds = odds_game()
    game.take_down_wager(odds)
    before = player.bankroll
    invalid = Wager(
        definition=defs.LINE_ODDS, 
        player=player,
        game=game, 
        value=value, 
        parent_wager=parent,
    )

    with pytest.raises((GameRuleViolation, ValueError)):
        game.place_wager(invalid)
    assert invalid not in game.wagers
    assert player.bankroll == before


def test_unaffordable_odds_rejected(odds_game: OddsFactory):
    game, player, parent, odds = odds_game()
    game.take_down_wager(odds)
    before = player.bankroll
    wager = Wager(
        definition=defs.LINE_ODDS, 
        player=player,
        game=game, 
        value=before + 1, 
        parent_wager=parent,
    )

    with pytest.raises(InsufficientFundsError):
        game.place_wager(wager)
    assert wager not in game.wagers
    assert player.bankroll == before


@pytest.mark.parametrize("parent_type", [WagerType.PASS_LINE, WagerType.COME])
def test_odds_require_established_parent_target(game_setup, parent_type):
    game, player = game_setup
    if parent_type is WagerType.PASS_LINE:
        parent = Wager(
            definition=defs.PASS_LINE, 
            player=player,
            game=game, 
            value=25,
        )

    else:
        game._point = 6
        parent = Wager(
            definition=defs.COME, 
            player=player,
            game=game, 
            value=25,
        )

    game.place_wager(parent)
    odds = Wager(
        definition=defs.LINE_ODDS, 
        player=player,
        game=game, 
        value=30, 
        parent_wager=parent,
    )

    before = player.bankroll
    with pytest.raises(GameRuleViolation):
        game.place_wager(odds)
    assert odds not in game.wagers
    assert player.bankroll == before


def test_odds_require_active_parent(game_setup):
    game, player = game_setup
    parent = Wager(
        definition=defs.COME, 
        player=player,
        game=game, 
        value=25, 
        target=6,
    )

    odds = Wager(
        definition=defs.LINE_ODDS, 
        player=player,
        game=game, 
        value=30, 
        parent_wager=parent,
    )
    
    with pytest.raises(GameRuleViolation):
        game.place_wager(odds)
    assert odds not in game.wagers
    assert player.bankroll == 1500


# -----------------------------------------------------------------------------
# RESOLUTION
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("parent_type", [WagerType.PASS_LINE, WagerType.COME])
@pytest.mark.parametrize("target", const.BOX_NUMS)
def test_working_odds_win_at_every_point(odds_game: OddsFactory, parent_type, target):
    game, _, _, odds = odds_game(target, parent_type)
    result = game._get_single_wager_result(odds, RollResult(target))
    assert result.resolution is Resolution.WIN


@pytest.mark.parametrize("parent_type", [WagerType.PASS_LINE, WagerType.COME])
@pytest.mark.parametrize("target", const.BOX_NUMS)
def test_working_odds_lose_on_seven(odds_game: OddsFactory, parent_type, target):
    game, _, _, odds = odds_game(target, parent_type)
    result = game._get_single_wager_result(odds, RollResult(7))
    assert result.resolution is Resolution.LOSE
    assert result.profit == 0


@pytest.mark.parametrize("roll", [2, 3, 5, 8, 9, 10, 11, 12])
def test_working_odds_ignore_other_rolls(odds_game: OddsFactory, roll):
    game, _, _, odds = odds_game(6)
    result = game._get_single_wager_result(odds, RollResult(roll))
    assert result.resolution is Resolution.NONE
    assert result.profit == 0


@pytest.mark.parametrize("parent_type", [WagerType.PASS_LINE, WagerType.COME])
@pytest.mark.parametrize("roll, expected", [
    (6, Resolution.REMOVE),
    (7, Resolution.REMOVE),
    (5, Resolution.NONE),
    (11, Resolution.NONE),
])
def test_nonworking_odds_follow_parent_resolution(
    odds_game: OddsFactory, parent_type, roll, expected
):
    game, _, _, odds = odds_game(6, parent_type)
    odds.is_working = False

    assert odds.is_working is False
    assert odds._is_working is False

    result = game._get_single_wager_result(
        odds, 
        RollResult(roll),
    )

    assert odds.is_working is False

    assert result.resolution is expected
    assert result.profit == 0


# -----------------------------------------------------------------------------
# PAYOUT
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("parent_type", [WagerType.PASS_LINE, WagerType.COME])
@pytest.mark.parametrize("target, expected", list(PROFIT_BY_POINT.items()))
def test_payout_matrix(odds_game: OddsFactory, parent_type, target, expected):
    game, _, _, odds = odds_game(target, parent_type)
    result = game._get_single_wager_result(odds, RollResult(target))
    assert result.resolution is Resolution.WIN
    assert result.profit == expected


@pytest.mark.parametrize("target, expected", [
    (4, 50), (5, 37), (6, 30), (8, 30), (9, 37), (10, 50)
])
def test_fractional_payouts_round_down(odds_game: OddsFactory, target, expected):
    game, _, _, odds = odds_game(target, WagerType.PASS_LINE, 25)
    assert game._get_single_wager_result(odds, RollResult(target)).profit == expected


# -----------------------------------------------------------------------------
# PERSISTENCE AND ACCOUNTING
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("parent_type", [WagerType.PASS_LINE, WagerType.COME])
def test_unresolved_odds_remain_active(
    odds_game: OddsFactory, 
    parent_type
) -> None:
    game, player, parent, odds = odds_game(6, parent_type)
    before = player.bankroll
    results = game.roll(9).wager_results
    assert result_for(results, odds).resolution is Resolution.NONE
    assert odds in game.wagers
    assert parent in game.wagers
    assert player.bankroll == before


@pytest.mark.parametrize("parent_type", [WagerType.PASS_LINE, WagerType.COME])
def test_odds_lose_and_stake_is_not_refunded(odds_game: OddsFactory, parent_type):
    game, player, parent, odds = odds_game(6, parent_type)
    results = game.roll(7).wager_results
    assert result_for(results, odds).resolution is Resolution.LOSE
    assert result_for(results, parent).resolution is Resolution.LOSE
    assert parent not in game.wagers
    assert odds not in game.wagers
    assert player.bankroll == 1500 - 25 - 30


@pytest.mark.parametrize("parent_type", [WagerType.PASS_LINE, WagerType.COME])
@pytest.mark.parametrize("target", const.BOX_NUMS)
def test_winning_odds_full_roll_pays_exactly_once(odds_game: OddsFactory, parent_type, target):
    game, player, parent, odds = odds_game(target, parent_type)
    results = game.roll(target).wager_results
    assert result_for(results, parent).resolution is Resolution.WIN
    assert result_for(results, odds).resolution is Resolution.WIN
    assert result_for(results, odds).profit == PROFIT_BY_POINT[target]
    assert odds not in game.wagers
    assert (parent in game.wagers) is (parent_type is WagerType.PASS_LINE)
    expected = 1500 + PROFIT_BY_POINT[target]
    if parent_type is WagerType.COME:
        expected += 25
    assert player.bankroll == expected


@pytest.mark.parametrize("parent_type", [WagerType.PASS_LINE, WagerType.COME])
def test_nonworking_odds_returned_once_on_parent_win(odds_game: OddsFactory, parent_type):
    game, player, parent, odds = odds_game(6, parent_type)
    odds.is_working = False
    results = game.roll(6).wager_results
    assert result_for(results, parent).resolution is Resolution.WIN
    odds_result = result_for(results, odds)
    assert odds_result.resolution is Resolution.REMOVE
    assert odds_result.profit == 0
    assert odds not in game.wagers
    assert (parent in game.wagers) is (parent_type is WagerType.PASS_LINE)
    expected = 1500
    if parent_type is WagerType.COME:
        expected += 25
    assert player.bankroll == expected


@pytest.mark.parametrize("parent_type", [WagerType.PASS_LINE, WagerType.COME])
def test_nonworking_odds_returned_once_on_parent_loss(odds_game: OddsFactory, parent_type):
    game, player, parent, odds = odds_game(6, parent_type)
    odds.is_working = False
    results = game.roll(7).wager_results
    assert result_for(results, parent).resolution is Resolution.LOSE
    assert result_for(results, odds).resolution is Resolution.REMOVE
    assert parent not in game.wagers
    assert odds not in game.wagers
    assert player.bankroll == 1500 - 25


def test_voluntary_odds_takedown_refunds_only_odds(odds_game: OddsFactory):
    game, player, parent, odds = odds_game(6)
    before = player.bankroll
    game.take_down_wager(odds)
    assert odds not in game.wagers
    assert parent in game.wagers
    assert game.get_child_wager(parent) is None
    assert player.bankroll == before + odds.value


def test_contracted_passline_cannot_be_taken_down_with_odds(odds_game: OddsFactory):
    game, player, parent, odds = odds_game(6)
    before = player.bankroll
    with pytest.raises(GameRuleViolation):
        game.take_down_wager(parent)
    assert parent in game.wagers
    assert odds in game.wagers
    assert player.bankroll == before


def test_forced_parent_takedown_does_not_cascade(odds_game: OddsFactory):
    game, player, parent, odds = odds_game(6)
    before = player.bankroll
    game._refund_wager(parent)
    assert parent not in game.wagers
    assert odds in game.wagers
    assert player.bankroll == before + parent.value
    # A forced parent takedown outside normal roll execution is not a valid
    # final table state. Odds resolve separately during normal game.roll().


def test_odds_value_can_be_increased_and_decreased(odds_game: OddsFactory):
    game, player, parent, odds = odds_game(6)
    game.increase_wager(odds, 10)
    assert odds.value == 40
    assert player.bankroll == 1435
    game.decrease_wager(odds, 15)
    assert odds.value == 25
    assert player.bankroll == 1450
    assert parent in game.wagers
    assert odds in game.wagers


def test_parent_decrease_does_not_modify_attached_odds(odds_game: OddsFactory):
    # A Come parent is contracted and cannot decrease; don't-side parent
    # reduction is covered in the lay-odds suite. Confirm at least that a
    # rejected line-parent reduction doesn't affect the attached odds.
    game, player, parent, odds = odds_game(6)
    before = player.bankroll
    with pytest.raises(GameRuleViolation):
        game.decrease_wager(parent, 5)
    assert parent.value == 25
    assert odds.value == 30
    assert parent in game.wagers and odds in game.wagers
    assert player.bankroll == before


# -----------------------------------------------------------------------------
# LIFECYCLE / RESULT-LIST INTEGRITY
# -----------------------------------------------------------------------------

def test_pass_line_odds_lifecycle(odds_game: OddsFactory):
    game, player, parent, odds = odds_game(6)
    assert player.bankroll == 1445
    assert odds.target == 6
    assert game.point == 6

    results = game.roll(5).wager_results
    assert result_for(results, parent).resolution is Resolution.NONE
    assert result_for(results, odds).resolution is Resolution.NONE
    assert player.bankroll == 1445

    results = game.roll(6).wager_results
    assert result_for(results, parent).resolution is Resolution.WIN
    assert result_for(results, odds).resolution is Resolution.WIN
    assert result_for(results, odds).profit == 36
    assert parent in game.wagers
    assert odds not in game.wagers
    assert game.point is None
    assert player.bankroll == 1536


def test_come_odds_lifecycle_with_comeout_off(odds_game: OddsFactory):
    game, player, parent, odds = odds_game(6, WagerType.COME)
    assert player.bankroll == 1445
    assert parent.target == odds.target == 6
    assert game.point != 6

    # Establishment of the table's next point does not change Come's target.
    # Instead of relying on automatic comeout configuration, toggle explicitly.
    odds.is_working = False
    results = game.roll(11).wager_results
    assert result_for(results, odds).resolution is Resolution.NONE
    assert parent in game.wagers
    assert odds in game.wagers
    assert player.bankroll == 1445

    results = game.roll(6).wager_results
    assert result_for(results, parent).resolution is Resolution.WIN
    assert result_for(results, odds).resolution is Resolution.REMOVE
    assert parent not in game.wagers
    assert odds not in game.wagers
    assert player.bankroll == 1525


def test_result_list_contains_independent_parent_and_odds_actions(odds_game: OddsFactory):
    game, player, parent, odds = odds_game(6, WagerType.COME)
    odds.is_working = False
    results = game.roll(6).wager_results
    relevant = [r for r in results if r.wager is parent or r.wager is odds]
    assert len(relevant) == 2
    assert {r.wager: r.resolution for r in relevant} == {
        parent: Resolution.WIN,
        odds: Resolution.REMOVE,
    }
    assert parent not in game.wagers
    assert odds not in game.wagers
    assert player.bankroll == 1525
