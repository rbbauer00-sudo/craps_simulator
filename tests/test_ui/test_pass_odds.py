
import pytest

from engine import WagerType
from ui.animations import AnimationMode


from .helpers import (
    click,
    select_chip,
    run_until_idle,
    force_roll,
)

pytestmark = pytest.mark.parametrize(
    "ui_app",
    list(AnimationMode),
    indirect=True,
)

@pytest.fixture
def pass_odds_game(ui_app):
    state = ui_app.states.current

    # Place $25 Pass Line.
    select_chip(state, 25)
    click(
        state,
        state.get_betting_area("PASS LINE").rect.center,
    )
    run_until_idle(state)

    parent = state.engine.get_wager(
        state.player,
        WagerType.PASS_LINE,
    )

    assert parent is not None

    # Establish point 6.
    force_roll(state, 6)
    assert state.engine.point == 6

    return state, parent


def test_odds_requires_point(ui_app, capsys):
    state = ui_app.states.current

    select_chip(state, 25)
    click(
        state,
        state.get_betting_area("PASS LINE").rect.center,
    )
    run_until_idle(state)

    parent = state.engine.get_wager(
        state.player,
        WagerType.PASS_LINE,
    )

    # Odds cannot be placed before a point.
    click(
        state, 
        state.get_betting_area("PASS ODDS").rect.center,      
    )

    assert state.engine.get_child_wager(parent) is None
    assert "Cannot change Pass Line odds:" in (
        capsys.readouterr().out
    )



def test_place_adjust_and_remove_odds(pass_odds_game):
    state, parent = pass_odds_game

    # Place $25 odds.
    odds_area = state.get_betting_area("PASS ODDS")

    select_chip(state, 25)
    click(state, odds_area.rect.center)
    run_until_idle(state)

    odds = state.engine.get_child_wager(parent)

    assert odds is not None
    assert odds.parent_wager is parent
    assert odds.value == 25
    assert odds.target == 6

    # Increase odds by $5.
    select_chip(state, 5)
    click(
        state,
        state.wager_sprites[odds].rect.center,
    )
    run_until_idle(state)

    assert odds.value == 30

    # Decrease odds by $5.
    click(
        state,
        state.wager_sprites[odds].rect.center,
        button=3,
    )
    run_until_idle(state)

    assert odds.value == 25

    # Remove odds by reducing to zero.
    select_chip(state, 100)
    click(
        state,
        state.wager_sprites[odds].rect.center,
        button=3,
    )
    run_until_idle(state)

    assert odds not in state.engine.wagers
    assert odds not in state.wager_sprites

    # Parent Pass Line remains contracted and active.
    assert parent in state.engine.wagers



def test_parent_cannot_be_removed_while_contracted(
    pass_odds_game,
    capsys,
):
    state, parent = pass_odds_game

    original_value = parent.value
    original_bankroll = state.player.bankroll

    select_chip(state, 100)
    click(
        state,
        state.wager_sprites[parent].rect.center,
        button=3,
    )
    run_until_idle(state)

    assert parent in state.engine.wagers
    assert parent.value == original_value
    assert state.player.bankroll == original_bankroll
    assert "Cannot modify wager:" in (
        capsys.readouterr().out
    )


@pytest.mark.parametrize("final_roll", [6, 7])
def test_parent_and_odds_resolve_together(
    pass_odds_game,
    final_roll,
):
    state, parent = pass_odds_game

    select_chip(state, 25)
    click(
        state, 
        state.get_betting_area("PASS ODDS").rect.center,
    )
    run_until_idle(state)

    odds = state.engine.get_child_wager(parent)
    assert odds is not None

    # Complete the hand by making the point
    # or sevening out.
    force_roll(state, final_roll)

    assert state.engine.point is None

    if final_roll == 6:
        # Pass Line wins and remains for the next come-out.
        assert parent in state.engine.wagers
        assert parent in state.wager_sprites

    else:
        # Seven-out removes the losing Pass Line.
        assert parent not in state.engine.wagers
        assert parent not in state.wager_sprites

    # Odds are removed on either win or loss.
    assert odds not in state.engine.wagers
    assert odds not in state.wager_sprites
   
    expected_bankroll = 1530 if final_roll == 6 else 1450

    assert state.player.bankroll == expected_bankroll
    assert state.player_sprite.displayed_bankroll == expected_bankroll