"""Long-running deterministic and randomized integration tests.

Run: pytest tests/test_game_stress.py -v

These use a local seeded RNG to drive Game.roll(d1, d2). This does NOT
change the Dice object's random seed or require a new Game constructor.
On failure, pytest includes the seed, iteration and recent actions.

Requires the invariant helper in tests/test_game_invariants.py; keep both
files in the same tests/ directory.
"""

from collections import Counter, deque
import random

import pytest
from test_game_invariants import assert_game_invariants

from engine import wager_definitions as defs
from engine.enums import Resolution
from engine.exceptions import GameRuleViolation
from engine.wager import Wager, WagerResult
from engine.game import Game


SEED_LONG = 0x1A75
SEED_ACTIVITY = 0xBEEF
SEED_MULTIPLAYER = 0xC0FFEE
BOX = (4, 5, 6, 8, 9, 10)
HARD = (4, 6, 8, 10)


def make_wager(game, player, definition, amount, *, target=None, parent=None):
    return Wager(
        game=game, player=player, definition=definition, value=amount,
        target=target, parent_wager=parent,
    )


def find_definition(*names):
    for name in names:
        candidate = getattr(defs, name, None)
        if candidate is not None:
            return candidate
    pytest.fail(f"No wager definition found among {names!r}")


def attempt_place(game, player, definition, amount, *, target=None, parent=None):
    """Expected rule rejections are fine; any other exception is a test failure."""
    wager = make_wager(game, player, definition, amount,
                       target=target, parent=parent)
    before = player.bankroll
    try:
        game.place_wager(wager)
    except GameRuleViolation:
        # Rejected placements should not debit the player or enter play.
        assert player.bankroll == before
        assert not any(w is wager for w in game.wagers)
        return None
    return wager


def assert_with_context(game, *, seed, step, recent):
    try:
        assert_game_invariants(game)
    except AssertionError as exc:
        pytest.fail(
            f"Invariant failed: seed={seed}, step={step}, "
            f"point={game.point}, recent={list(recent)!r}\n{exc}",
            pytrace=True,
        )


def random_dice(rng):
    return rng.randint(1, 6), rng.randint(1, 6)


def do_roll(
        game: Game, 
        rng, 
        *, 
        seed, 
        step, 
        recent, 
        counts,
) -> list[WagerResult]:
    d1, d2 = random_dice(rng)
    previous = list(game.wagers)
    recent.append((step, "roll", d1, d2, game.point))
    try:
        results = list(game.roll(d1, d2).wager_results)
    except Exception as exc:
        pytest.fail(
            f"Roll raised {type(exc).__name__}: {exc}; seed={seed} "
            f"step={step}, recent={list(recent)!r}"
        )
    counts[d1 + d2] += 1
    # A wager must not be resolved twice in the same roll. No new wager
    # may appear automatically during execution.
    assert len(results) == len({id(r.wager) for r in results})
    assert all(any(r.wager is w for w in previous) for r in results)
    assert all(r.resolution in Resolution for r in results)
    assert_with_context(game, seed=seed, step=step, recent=recent)
    return results


def random_action(game, player, rng, *, seed, step, recent):
    """Random legal-or-rejected player action, with low risk of bankroll ruin.

    Simulates user activity, not a profitable betting strategy. Candidate bets
    are deliberately limited to wager types whose constructor is established.
    """
    mine = [w for w in game.wagers if w.player is player]
    action = rng.choice(("place", "place", "place", "remove", "remove"))

    if action == "remove" and mine:
        # Try removal even if contracted; rejection must leave state unchanged.
        wager = rng.choice(mine)
        before = player.bankroll
        recent.append((step, "take_down", wager.definition.name, wager.value))
        try:
            game.take_down_wager(wager)
        except GameRuleViolation:
            assert any(w is wager for w in game.wagers)
            assert player.bankroll == before
        assert_with_context(game, seed=seed, step=step, recent=recent)
        return

    if player.bankroll < 5:
        assert_with_context(game, seed=seed, step=step, recent=recent)
        return

    wager_kind = rng.choice(("field", "line", "place", "hard"))
    definition, target = {
        "field": (defs.FIELD, None),
        "line": (defs.PASS_LINE, None),
        "place": (find_definition("PLACE", "PLACE_BET"), rng.choice(BOX)),
        "hard": (find_definition("HARDWAY", "HARDWAYS", "HARD_6", "HARD_SIX"),
                 rng.choice(HARD)),
    }[wager_kind]
    amount = min(5 if wager_kind != "place" else 30, player.bankroll)
    # Place 6/8 requires multiples of 6, other places sometimes multiples of 5;
    # rejected amounts are legitimate negative tests, not fatal errors.
    recent.append((step, "place", wager_kind, target, amount))
    attempt_place(game, player, definition, amount, target=target)
    assert_with_context(game, seed=seed, step=step, recent=recent)


def test_long_deterministic_session_1000_rolls(game_setup):
    """All game invariants hold for a replayable 1,000-roll session."""
    game, player = game_setup
    rng = random.Random(SEED_LONG)
    recent = deque(maxlen=15)
    counts = Counter()

    # One recurring line bet exercises point, contract and shooter transitions.
    line = attempt_place(game, player, defs.PASS_LINE, 25)
    assert line is not None
    for step in range(1, 1001):
        do_roll(game, rng, seed=SEED_LONG, step=step,
                recent=recent, counts=counts)
        if not any(w is line for w in game.wagers) and game.point is None:
            line = attempt_place(game, player, defs.PASS_LINE, 25)
            assert_with_context(game, seed=SEED_LONG, step=step, recent=recent)

    assert sum(counts.values()) == 1000
    assert set(counts) <= set(range(2, 13))
    assert sum(counts.values()) == 1000


@pytest.mark.parametrize("seed", (SEED_ACTIVITY, 0x1234))
def test_randomized_actions_and_rolls_2500_each(game_setup, seed):
    """Seeded field/line/place/hardway activity with state checks after actions."""
    game, player = game_setup
    rng = random.Random(seed)
    recent = deque(maxlen=20)
    counts = Counter()

    for step in range(1, 2501):
        # Different numbers of between-roll actions exercise duplicate/contract
        # rejection and proper cleanup while the shooter continues.
        for _ in range(rng.randrange(3)):
            random_action(game, player, rng, seed=seed,
                          step=step, recent=recent)
        do_roll(game, rng, seed=seed, step=step,
                recent=recent, counts=counts)

    assert sum(counts.values()) == 2500


def test_multi_player_randomized_session_2000_rolls(game_setup):
    """Three players share one table but cannot mutate one another's wagers."""
    game, first = game_setup
    players = [first, game.add_player(), game.add_player()]
    rng = random.Random(SEED_MULTIPLAYER)
    recent = deque(maxlen=20)
    counts = Counter()

    for step in range(1, 2001):
        player = rng.choice(players)
        random_action(game, player, rng, seed=SEED_MULTIPLAYER,
                      step=step, recent=recent)
        do_roll(game, rng, seed=SEED_MULTIPLAYER, step=step,
                recent=recent, counts=counts)
        assert all(any(w.player is p for p in players) for w in game.wagers)

    assert sum(counts.values()) == 2000
    assert len(game.players) == 3
