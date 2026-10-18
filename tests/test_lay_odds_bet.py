
import pytest
from conftest import result_for
from collections.abc import Callable

from engine import constants as const
from engine import wager_definitions as defs
from engine.game import Game
from engine.player import Player
from engine.wager import Wager
from engine.dice import RollResult
from engine.enums import Resolution, WagerType
from engine.exceptions import GameRuleViolation, InsufficientFundsError


PROFIT_BY_POINT = {4: 15, 5: 20, 6: 25, 8: 25, 9: 20, 10: 15}

OddsSetup = tuple[Game, Player, Wager, Wager]
OddsFactory = Callable[..., OddsSetup]


@pytest.fixture
def odds_game(game_setup: tuple[Game, Player]) -> OddsFactory:
    game, player = game_setup

    def _setup(
        target: int = 6,
        parent_type: WagerType = WagerType.DONT_PASS,
        odds_value: int = 30,
    ) -> OddsSetup:
        assert target in const.BOX_NUMS

        if parent_type is WagerType.DONT_PASS:
            parent = Wager(
                definition=defs.DONT_PASS, 
                player=player,
                game=game,
                value=25,
            )

            game.place_wager(parent)
            game.roll(target)
            assert game.point == target

        elif parent_type is WagerType.DONT_COME:
            # Don't Come is booked with the table point ON, then travels.
            game._point = 5 if target != 5 else 6
            parent = Wager(
                definition=defs.DONT_COME, 
                player=player,
                game=game, 
                value=25,
            )

            game.place_wager(parent)
            game.roll(target)
            assert parent.target == target
            assert game.point != target

        else:
            raise ValueError(f"Unsupported parent type: {parent_type}")

        odds = Wager(
            definition=defs.LAY_ODDS,
            player=player,
            game=game,
            value=odds_value,
            parent_wager=parent,
        )
        game.place_wager(odds)
        return game, player, parent, odds

    return _setup



# =============================================================================
# DEFINITION
# =============================================================================

def test_wager_definition():
    assert defs.LAY_ODDS.wager_type is WagerType.LAY_ODDS
    assert defs.LAY_ODDS.name == "Lay Odds"
    assert defs.LAY_ODDS.can_turn_off is True
    assert defs.LAY_ODDS.remove_after_win is True


# =============================================================================
# PLACEMENT
# =============================================================================

@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
@pytest.mark.parametrize("target", const.BOX_NUMS)
def test_placement_assigns_parent_and_target(odds_game: OddsFactory, parent_type, target):
    game, player, parent, odds = odds_game(target, parent_type)
    assert odds in game.wagers
    assert odds in player.get_wagers()
    assert odds.parent_wager is parent
    assert odds.target == target
    assert game.get_child_wager(parent) is odds
    assert player.bankroll == 1500 - 25 - 30


@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
def test_duplicate_odds_rejected_without_charging(odds_game: OddsFactory, parent_type):
    game, player, parent, odds = odds_game(6, parent_type)
    before = player.bankroll
    duplicate = Wager(
        definition=defs.LAY_ODDS, 
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
        definition=defs.LAY_ODDS, 
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
    invalid = Wager(
        definition=defs.LAY_ODDS, 
        player=player,
        game=game,
        value=before + 1, 
        parent_wager=parent,
    )

    with pytest.raises(InsufficientFundsError):
        game.place_wager(invalid)
    assert invalid not in game.wagers
    assert player.bankroll == before


@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
def test_odds_require_established_parent_target(game_setup, parent_type):
    game, player = game_setup
    if parent_type is WagerType.DONT_PASS:
        parent = Wager(
            definition=defs.DONT_PASS, 
            player=player,
            game=game, 
            value=25,
        )

    else:
        game._point = 6
        parent = Wager(
            definition=defs.DONT_COME, 
            player=player,
            game=game, 
            value=25,
        )
        
    game.place_wager(parent)
    odds = Wager(
        definition=defs.LAY_ODDS, 
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
        definition=defs.DONT_COME, 
        player=player,
        game=game, 
        value=25, 
        target=6,
        )
    
    odds = Wager(
        definition=defs.LAY_ODDS, 
        player=player,
        game=game,
        value=30, 
        parent_wager=parent,
    )

    with pytest.raises(GameRuleViolation):
        game.place_wager(odds)
    assert odds not in game.wagers
    assert player.bankroll == 1500


def test_odds_require_parent_reference(game_setup):
    game, player = game_setup
    odds = Wager(
        definition=defs.LAY_ODDS, 
        player=player,
        game=game, 
        value=30,
    )

    with pytest.raises(ValueError):
        game.place_wager(odds)
    assert odds not in game.wagers
    assert player.bankroll == 1500


def test_replacement_odds_allowed_after_voluntary_removal(odds_game: OddsFactory):
    game, player, parent, old_odds = odds_game()
    game.take_down_wager(old_odds)
    new_odds = Wager(
        definition=defs.LAY_ODDS, 
        player=player,
        game=game,
        value=40, 
        parent_wager=parent,
    )

    game.place_wager(new_odds)
    assert old_odds not in game.wagers
    assert game.get_child_wager(parent) is new_odds
    assert new_odds.target == 6
    assert player.bankroll == 1500 - 25 - 40


# =============================================================================
# RESOLUTION
# =============================================================================
@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
@pytest.mark.parametrize("target", const.BOX_NUMS)
def test_working_lay_odds_win_on_seven(odds_game: OddsFactory, parent_type, target):
    game, _, _, odds = odds_game(target, parent_type)
    result = game._get_single_wager_result(odds, RollResult(7))
    assert result.resolution is Resolution.WIN
    assert result.profit == PROFIT_BY_POINT[target]


@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
@pytest.mark.parametrize("target", const.BOX_NUMS)
def test_working_lay_odds_lose_at_parent_point(odds_game: OddsFactory, parent_type, target):
    game, _, _, odds = odds_game(target, parent_type)
    result = game._get_single_wager_result(odds, RollResult(target))
    assert result.resolution is Resolution.LOSE
    assert result.profit == 0


@pytest.mark.parametrize("roll", [2, 3, 4, 5, 8, 9, 10, 11, 12])
def test_working_odds_ignore_other_rolls(odds_game: OddsFactory, roll):
    game, _, _, odds = odds_game(6)
    result = game._get_single_wager_result(odds, RollResult(roll))
    assert result.resolution is Resolution.NONE
    assert result.profit == 0


@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
@pytest.mark.parametrize("roll, expected", [
    (7, Resolution.REMOVE),
    (6, Resolution.REMOVE),
    (5, Resolution.NONE),
    (11, Resolution.NONE),
])
def test_nonworking_odds_follow_parent_resolution(
    odds_game: OddsFactory, parent_type, roll, expected
):
    game, _, _, odds = odds_game(6, parent_type)
    odds.is_working = False
    result = game._get_single_wager_result(odds, RollResult(roll))
    assert result.resolution is expected
    assert result.profit == 0
    assert odds.is_working is False


def test_nonworking_odds_can_be_reenabled(odds_game: OddsFactory):
    game, _, _, odds = odds_game(6)
    odds.is_working = False
    assert game._get_single_wager_result(odds, RollResult(7)).resolution is Resolution.REMOVE
    odds.is_working = True
    assert game._get_single_wager_result(odds, RollResult(7)).resolution is Resolution.WIN


# =============================================================================
# PAYOUT
# =============================================================================

@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
@pytest.mark.parametrize("target, expected", list(PROFIT_BY_POINT.items()))
def test_payout_matrix(odds_game: OddsFactory, parent_type, target, expected):
    game, _, _, odds = odds_game(target, parent_type)
    result = game._get_single_wager_result(odds, RollResult(7))
    assert result.resolution is Resolution.WIN
    assert result.profit == expected


@pytest.mark.parametrize("target, expected", [
    (4, 12), (5, 16), (6, 20), (8, 20), (9, 16), (10, 12)
])
def test_fractional_payouts_round_down(odds_game: OddsFactory, target, expected):
    game, _, _, odds = odds_game(target, WagerType.DONT_PASS, 25)
    assert game._get_single_wager_result(odds, RollResult(7)).profit == expected


def test_payout_does_not_depend_on_current_table_point(odds_game: OddsFactory):
    game, _, parent, odds = odds_game(4, WagerType.DONT_COME)
    assert game.point != parent.target
    assert game._get_single_wager_result(odds, RollResult(7)).profit == 15


# =============================================================================
# PERSISTENCE / ACCOUNTING
# =============================================================================

@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
def test_unresolved_odds_remain_active(odds_game: OddsFactory, parent_type):
    game, player, parent, odds = odds_game(6, parent_type)
    before = player.bankroll
    results = game.roll(9).wager_results
    assert result_for(results, odds).resolution is Resolution.NONE
    assert parent in game.wagers
    assert odds in game.wagers
    assert player.bankroll == before


@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
def test_losing_odds_stake_not_refunded(odds_game: OddsFactory, parent_type):
    game, player, parent, odds = odds_game(6, parent_type)
    results = game.roll(6).wager_results
    assert result_for(results, parent).resolution is Resolution.LOSE
    assert result_for(results, odds).resolution is Resolution.LOSE
    assert parent not in game.wagers
    assert odds not in game.wagers
    assert player.bankroll == 1500 - 25 - 30


@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
@pytest.mark.parametrize("target", const.BOX_NUMS)
def test_winning_odds_full_roll_pays_exactly_once(
    odds_game: OddsFactory, parent_type, target
):
    game, player, parent, odds = odds_game(target, parent_type)
    results = game.roll(7).wager_results
    assert result_for(results, parent).resolution is Resolution.WIN
    assert result_for(results, odds).resolution is Resolution.WIN
    assert result_for(results, odds).profit == PROFIT_BY_POINT[target]
    assert odds not in game.wagers
    assert (parent in game.wagers) is (parent_type is WagerType.DONT_PASS)
    expected = 1500 + PROFIT_BY_POINT[target]
    if parent_type is WagerType.DONT_COME:
        expected += 25
    assert player.bankroll == expected


@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
def test_nonworking_odds_refunded_once_on_parent_win(odds_game: OddsFactory, parent_type):
    game, player, parent, odds = odds_game(6, parent_type)
    odds.is_working = False
    results = game.roll(7).wager_results
    assert result_for(results, parent).resolution is Resolution.WIN
    assert result_for(results, odds).resolution is Resolution.REMOVE
    assert result_for(results, odds).profit == 0
    assert odds not in game.wagers
    assert (parent in game.wagers) is (parent_type is WagerType.DONT_PASS)
    expected = 1500
    if parent_type is WagerType.DONT_COME:
        expected += 25
    assert player.bankroll == expected


@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
def test_nonworking_odds_refunded_once_on_parent_loss(odds_game: OddsFactory, parent_type):
    game, player, parent, odds = odds_game(6, parent_type)
    odds.is_working = False
    results = game.roll(6).wager_results
    assert result_for(results, parent).resolution is Resolution.LOSE
    assert result_for(results, odds).resolution is Resolution.REMOVE
    assert parent not in game.wagers
    assert odds not in game.wagers
    assert player.bankroll == 1500 - 25


# =============================================================================
# TAKEDOWN / ADJUSTMENTS
# =============================================================================

def test_voluntary_odds_takedown_refunds_only_odds(odds_game: OddsFactory):
    game, player, parent, odds = odds_game()
    before = player.bankroll
    game.take_down_wager(odds)
    assert odds not in game.wagers
    assert parent in game.wagers
    assert game.get_child_wager(parent) is None
    assert player.bankroll == before + odds.value


@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
def test_voluntary_parent_takedown_cascades_refund(odds_game: OddsFactory, parent_type):
    game, player, parent, odds = odds_game(6, parent_type)
    game.take_down_wager(parent)
    assert parent not in game.wagers
    assert odds not in game.wagers
    assert player.bankroll == 1500


def test_forced_parent_takedown_does_not_cascade(odds_game: OddsFactory):
    game, player, parent, odds = odds_game(6)
    before = player.bankroll
    game._refund_wager(parent)
    assert parent not in game.wagers
    assert odds in game.wagers
    assert player.bankroll == before + parent.value
    # This intermediate state is intentional only for isolated testing:
    # during game.roll(), the odds resolve through their own result.


@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
def test_decreasing_parent_preserves_odds(odds_game: OddsFactory, parent_type):
    game, player, parent, odds = odds_game(6, parent_type)
    before = player.bankroll
    game.decrease_wager(parent, 10)
    assert parent.value == 15
    assert odds.value == 30
    assert odds.parent_wager is parent
    assert parent in game.wagers
    assert odds in game.wagers
    assert player.bankroll == before + 10


def test_parent_decrease_does_not_limit_odds_by_ratio(odds_game: OddsFactory):
    # Casino-defined odds maxima are UI policy; no engine ratio enforcement.
    game, player, parent, odds = odds_game(6, WagerType.DONT_PASS)
    game.decrease_wager(parent, 20)
    assert parent.value == 5
    assert odds.value == 30
    assert odds in game.wagers
    assert player.bankroll == 1500 - 5 - 30


@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
def test_decrease_to_zero_routes_through_parent_takedown(odds_game: OddsFactory, parent_type):
    game, player, parent, odds = odds_game(6, parent_type)
    game.decrease_wager(parent, parent.value)
    assert parent not in game.wagers
    assert odds not in game.wagers
    assert player.bankroll == 1500


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


# =============================================================================
# LIFECYCLE / ANIMATION RESULT INTEGRITY
# =============================================================================

def test_dont_pass_lay_odds_lifecycle(odds_game: OddsFactory):
    game, player, parent, odds = odds_game(6)
    assert game.point == 6
    assert odds.target == 6
    assert player.bankroll == 1445

    results = game.roll(5).wager_results
    assert result_for(results, parent).resolution is Resolution.NONE
    assert result_for(results, odds).resolution is Resolution.NONE
    assert player.bankroll == 1445

    results = game.roll(7).wager_results
    assert result_for(results, parent).resolution is Resolution.WIN
    assert result_for(results, odds).resolution is Resolution.WIN
    assert result_for(results, odds).profit == 25
    assert parent in game.wagers  # Don't Pass stays up after win
    assert odds not in game.wagers
    assert game.point is None
    assert player.bankroll == 1525


def test_dont_come_lay_odds_lifecycle(odds_game: OddsFactory):
    game, player, parent, odds = odds_game(6, WagerType.DONT_COME)
    assert parent.target == odds.target == 6
    assert player.bankroll == 1445

    results = game.roll(9).wager_results
    assert result_for(results, parent).resolution is Resolution.NONE
    assert result_for(results, odds).resolution is Resolution.NONE
    assert parent in game.wagers and odds in game.wagers

    results = game.roll(7).wager_results
    assert result_for(results, parent).resolution is Resolution.WIN
    assert result_for(results, odds).resolution is Resolution.WIN
    assert parent not in game.wagers
    assert odds not in game.wagers
    assert player.bankroll == 1550


@pytest.mark.parametrize("parent_type", [WagerType.DONT_PASS, WagerType.DONT_COME])
def test_result_list_contains_independent_parent_and_odds_actions(
    odds_game: OddsFactory, parent_type
):
    game, player, parent, odds = odds_game(6, parent_type)
    odds.is_working = False
    results = game.roll(7).wager_results
    relevant = [r for r in results if r.wager is parent or r.wager is odds]
    assert len(relevant) == 2
    assert {r.wager: r.resolution for r in relevant} == {
        parent: Resolution.WIN, odds: Resolution.REMOVE,
    }
    assert odds not in game.wagers
    expected = 1500 + (25 if parent_type is WagerType.DONT_COME else 0)
    assert player.bankroll == expected
