"""Public API freeze regression tests for the craps engine.

Assumes the current API discussed in October 2026:
  * Game.roll() -> frozen GameRollResult
  * Game.reset(settings=..., seed=..., predetermined_rolls=...)
  * Game.remove_player() -> frozen PlayerResult
  * Game.players / wagers / point / shooter_roll_count / settings are read-only
  * Wager objects are constructed by callers, then placed through Game.

No conftest.py fixtures are required.
"""

from dataclasses import FrozenInstanceError, replace

import pytest

from engine.dice import RollResult
from engine.enums import Resolution, VigSetting
from engine.exceptions import EngineStateError, GameRuleViolation, InsufficientFundsError
from engine.game import Game, GameRollResult, GameSettings
from engine.player import PlayerResult
from engine.wager import Wager, WagerResult
from engine import wager_definitions as defs


def wager_for(game, player, definition, value=25, *, target=None, parent=None):
    return Wager(
        game=game,
        player=player,
        definition=definition,
        value=value,
        target=target,
        parent_wager=parent,
    )


def placed(game, player, definition, value=25, *, target=None, parent=None):
    wager = wager_for(game, player, definition, value, target=target, parent=parent)
    game.place_wager(wager)
    return wager


def result_for(roll_result: GameRollResult, wager: Wager) -> WagerResult:
    matches = [r for r in roll_result.wager_results if r.wager is wager]
    assert len(matches) == 1, f"Expected exactly one result for {wager!r}, got {len(matches)}"
    return matches[0]


# 1. RESET, CONFIGURATION AND DICE REPLACEMENT

def test_reset_clears_active_session_and_preserves_settings_by_default():
    settings = GameSettings(buy_vig_setting=VigSetting.ON_WIN)
    game = Game(settings=settings, seed=12345)
    player = game.add_player("Old player")
    placed(game, player, defs.PASS_LINE)
    game.roll(6)
    assert game.point == 6
    assert game.wagers

    game.reset(seed=67890)

    assert game.point is None
    assert game.shooter_roll_count == 0
    assert game.players == ()
    assert game.wagers == ()
    assert game.settings is settings
    assert game.roll(7).point_before is None


def test_reset_replaces_settings_and_uses_new_predetermined_rolls():
    game = Game(seed=111)
    new_settings = replace(game.settings, field_3x_on_12=False)
    game.reset(settings=new_settings, seed=222, predetermined_rolls=[(2, 3)])
    assert game.settings is new_settings
    result = game.roll()
    assert result.roll.total == 5
    assert result.roll.as_tuple == (2, 3)


@pytest.mark.parametrize("invalid_rolls", [[(0, 3)], [(7, 1)], [13]])
def test_failed_reset_does_not_change_live_game(invalid_rolls):
    game = Game(seed=123)
    player = game.add_player()
    wager = placed(game, player, defs.PASS_LINE)
    game.roll(6)
    original = (game.settings, game.players, game.wagers, game.point,
                game.shooter_roll_count)

    with pytest.raises((ValueError, TypeError)):
        game.reset(predetermined_rolls=invalid_rolls)

    assert (game.settings, game.players, game.wagers, game.point,
            game.shooter_roll_count) == original
    assert wager in game.wagers


def test_frozen_settings_require_replace_and_reset():
    game = Game()
    old = game.settings
    with pytest.raises(FrozenInstanceError):
        game.settings.field_3x_on_12 = False
    with pytest.raises(AttributeError):
        game.settings = GameSettings(field_3x_on_12=False)
    assert game.settings is old
    new = replace(old, field_3x_on_12=False)
    game.reset(settings=new)
    assert game.settings is new


# 2. PLAYER REMOVAL AND ACCOUNTING

def test_remove_player_refunds_uncontracted_wagers_and_reports_result():
    game = Game()
    player = game.add_player("Leaving", bankroll=1500)
    placed(game, player, defs.PLACE_BET, 24, target=6)
    assert player.bankroll == 1476

    result = game.remove_player(player)

    assert isinstance(result, PlayerResult)
    assert result.name == "Leaving"
    assert result.final_bankroll == 1500
    assert result.forfeited_value == 0
    assert player not in game.players
    assert all(w.player is not player for w in game.wagers)


def test_remove_player_refunds_odds_and_forfeits_only_pass_line_contract():
    game = Game()
    player = game.add_player("Leaving", bankroll=1500)
    parent = placed(game, player, defs.PASS_LINE, 25)
    game.roll(6)
    assert parent.contract_min == 25
    odds = placed(game, player, defs.LINE_ODDS, 30, parent=parent)
    assert player.bankroll == 1445

    result = game.remove_player(player)

    assert result.final_bankroll == 1475  # Odds refunded, contracted $25 forfeited
    assert result.forfeited_value == 25
    assert not game.wagers
    assert not game.players
    assert odds not in game.wagers



def test_remove_player_rejects_unregistered_player_without_mutation():
    game = Game()
    other_game = Game()
    foreign_player = other_game.add_player()
    local = game.add_player()
    before = game.players
    with pytest.raises(ValueError):
        game.remove_player(foreign_player)
    assert game.players == before == (local,)


def test_player_result_is_frozen():
    game = Game()
    p = game.add_player()
    result = game.remove_player(p)
    with pytest.raises(FrozenInstanceError):
        result.final_bankroll = 123


# 3. REJECTED PLAYER ACTIONS LEAVE STATE UNCHANGED

def test_invalid_duplicate_bet_does_not_charge_or_add_wager():
    game = Game()
    player = game.add_player()
    original = placed(game, player, defs.FIELD)
    before = player.bankroll
    duplicate = wager_for(game, player, defs.FIELD)
    with pytest.raises(GameRuleViolation):
        game.place_wager(duplicate)
    assert game.wagers == (original,)
    assert player.bankroll == before


def test_insufficient_funds_does_not_book_wager():
    game = Game()
    player = game.add_player(bankroll=20)
    wager = wager_for(game, player, defs.FIELD, 25)
    with pytest.raises(InsufficientFundsError):
        game.place_wager(wager)
    assert game.wagers == ()
    assert player.bankroll == 20


def test_invalid_ownership_does_not_book_wager_or_charge():
    one, two = Game(), Game()
    owner = one.add_player()
    before = owner.bankroll
    bad_wager = wager_for(two, owner, defs.FIELD)
    with pytest.raises(ValueError):
        two.place_wager(bad_wager)
    assert not one.wagers and not two.wagers
    assert owner.bankroll == before


def test_contracted_takedown_rejected_without_refunding_odds():
    game = Game()
    player = game.add_player()
    parent = placed(game, player, defs.PASS_LINE)
    game.roll(6)
    odds = placed(game, player, defs.LINE_ODDS, 30, parent=parent)
    before = player.bankroll
    with pytest.raises(GameRuleViolation):
        game.take_down_wager(parent)
    assert game.wagers == (parent, odds)
    assert player.bankroll == before


def test_failed_increase_does_not_change_value_or_bankroll():
    game = Game()
    player = game.add_player(bankroll=50)
    bet = placed(game, player, defs.FIELD, 25)
    with pytest.raises(InsufficientFundsError):
        game.increase_wager(bet, 26)
    assert bet.value == 25
    assert player.bankroll == 25
    assert game.wagers == (bet,)


# 4. INVALID DICE INPUT IS FATAL AND DOES NOT ADVANCE SESSION

@pytest.mark.parametrize("d1,d2", [(8, 2), (0, 4), (7, 3), (None, 3), (13, None)])
def test_invalid_roll_arguments_propagate_and_do_not_advance_game(d1, d2):
    game = Game(seed=97531)
    player = game.add_player()
    bet = placed(game, player, defs.FIELD)
    before = (game.point, game.shooter_roll_count, game.wagers, player.bankroll)
    with pytest.raises((ValueError, TypeError)):
        game.roll(d1, d2)
    assert (game.point, game.shooter_roll_count, game.wagers, player.bankroll) == before
    assert bet in game.wagers


def test_invalid_roll_does_not_consume_seeded_rng():
    a, b = Game(seed=2026), Game(seed=2026)
    with pytest.raises((ValueError, TypeError)):
        a.roll(8, 2)
    # Two valid random rolls must remain in lockstep after the rejected request.
    assert a.roll().roll.as_tuple == b.roll().roll.as_tuple
    assert a.roll().roll.as_tuple == b.roll().roll.as_tuple


def test_remove_player_only_affects_that_player_and_preserves_ids():
    game = Game()
    a = game.add_player("A")
    b = game.add_player("B")
    c = game.add_player("C")

    other_wager = placed(
        game, c, defs.PLACE_BET, 24, target=6
    )
    c_before = c.bankroll

    result = game.remove_player(b)

    assert isinstance(result, PlayerResult)
    assert game.players == (a, c)

    # Player IDs remain unchanged
    assert (a.id, c.id) == (0, 2)

    # Other player's wagers and bankroll unaffected
    assert other_wager in game.wagers
    assert c.bankroll == c_before

    # New player receives a new ID
    d = game.add_player("D")

    assert game.players == (a, c, d)
    assert (a.id, c.id, d.id) == (0, 2, 3)


def test_player_position_independent_of_id():
    game = Game()

    a = game.add_player("A")
    b = game.add_player("B")
    c = game.add_player("C")

    game.remove_player(b)

    assert game.players.index(a) == 0
    assert game.players.index(c) == 1

    assert a.id == 0
    assert c.id == 2



def test_game_roll_result_point_transitions_and_seven_out():
    game = Game()
    comeout = game.roll(6)
    assert isinstance(comeout, GameRollResult)
    assert (comeout.point_before, comeout.point_after, comeout.seven_out) == (None, 6, False)
    assert comeout.shooter_roll_count == 1
    assert comeout.wager_results == ()

    seven_out = game.roll(7)
    assert (seven_out.point_before, seven_out.point_after, seven_out.seven_out) == (6, None, True)
    assert seven_out.shooter_roll_count == 2
    assert game.shooter_roll_count == 0
    assert comeout.point_after == 6  # Previous result cannot change


def test_comeout_seven_is_not_a_seven_out():
    game = Game()
    result = game.roll(7)
    assert result.point_before is None
    assert result.point_after is None
    assert result.seven_out is False


def test_game_roll_result_and_wager_results_are_frozen():
    game = Game()
    player = game.add_player()
    bet = placed(game, player, defs.FIELD)
    roll = game.roll(3)
    result = result_for(roll, bet)
    assert isinstance(roll.wager_results, tuple)
    assert isinstance(result, WagerResult)
    with pytest.raises(FrozenInstanceError):
        roll.point_after = 4
    with pytest.raises(FrozenInstanceError):
        result.profit = 999


def test_previous_wager_result_is_preserved_after_later_roll():
    game = Game()
    player = game.add_player()
    bet = placed(game, player, defs.PASS_LINE)
    first = game.roll(6)
    first_result = result_for(first, bet)
    assert first_result.resolution is Resolution.NONE
    assert first.point_after == 6
    second = game.roll(7)
    assert result_for(second, bet).resolution is Resolution.LOSE
    assert first_result.resolution is Resolution.NONE
    assert first.point_after == 6
    assert bet not in game.wagers


# 6. READ-ONLY EXTERNAL GAME BOUNDARIES / ENGINE INVARIANTS

def test_public_game_collections_cannot_be_mutated_directly():
    game = Game()
    player = game.add_player()
    assert game.players == (player,)
    with pytest.raises(AttributeError):
        game.players.append(player)
    with pytest.raises(AttributeError):
        game.wagers.clear()
    with pytest.raises(AttributeError):
        game.point = 6
    with pytest.raises(AttributeError):
        game.shooter_roll_count = 99
    assert game.players == (player,)
    assert game.wagers == ()
    assert game.point is None
    assert game.shooter_roll_count == 0


def test_result_validator_catches_duplicate_missing_and_invalid_results():
    game = Game()
    player = game.add_player()
    a = placed(game, player, defs.PLACE_BET, 24, target=6)
    b = placed(game, player, defs.PLACE_BET, 25, target=8)
    good_a = WagerResult(a, Resolution.NONE)
    good_b = WagerResult(b, Resolution.NONE)

    game._validate_roll_results([good_a, good_b])
    for invalid in ([good_a], [good_a, good_a], [good_a, None],
                    [good_a, WagerResult(b, Resolution.MOVE, move_to=3)]):
        with pytest.raises(EngineStateError):
            game._validate_roll_results(invalid)


def test_player_removal_then_roll_has_no_orphaned_wagers():
    game = Game()
    departing = game.add_player()
    survivor = game.add_player()
    placed(game, departing, defs.PASS_LINE)
    game.roll(6)
    placed(game, survivor, defs.PLACE_BET, 24, target=8)
    game.remove_player(departing)
    assert all(w.player is survivor for w in game.wagers)
    game.roll(7)  # Must not resolve a wager belonging to a removed player.
    assert game.wagers == ()
