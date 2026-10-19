
from dataclasses import dataclass, replace

from engine import Resolution, Game, Wager, Resolution, defs
from engine.game import GameSettings
from engine.enums import VigSetting
from simulator import Simulator, SessionStatistics, WagerChangeType


@dataclass(frozen=True)
class RollFinancials:
    equity_change: int
    resolution_net: int
    residual: int


def get_roll_financials(record, player_id: int) -> RollFinancials:
    before = next(
        p.equity.total_equity
        for p in record.players_before
        if p.player_id == player_id
    )

    after = next(
        p.equity.total_equity
        for p in record.players_after
        if p.player_id == player_id
    )

    wagers = {
        w.wager_id: w
        for w in record.wagers_before
    }

    resolution_net = 0

    for outcome in record.wager_outcomes:
        wager = wagers[outcome.wager_id]

        if wager.player_id != player_id:
            continue

        if outcome.resolution is Resolution.WIN:
            resolution_net += outcome.profit

        elif outcome.resolution is Resolution.LOSE:
            resolution_net -= wager.value

    equity_change = after - before

    return RollFinancials(
        equity_change=equity_change,
        resolution_net=resolution_net,
        residual=resolution_net - equity_change,
    )


def assert_roll_accounting(
    record,
    player_id: int,
    expected_residual: int,
):
    financials = get_roll_financials(
        record, player_id
    )

    assert financials.residual == expected_residual


def assert_no_uncommitted_cost(
    game,
    player,
    make_adjustments,
):
    equity_before = player.get_equity().total_equity

    # Place, adjust, and cancel before a roll.
    make_adjustments()

    equity_after = player.get_equity().total_equity

    assert equity_after == equity_before


from engine import Game, Wager, defs
from simulator import Simulator


# ========================
# NO-VIG BASELINE
# ========================

def test_no_vig_baseline():
    game = Game(predetermined_rolls=[
        (2, 2),  # Establish point 4
        (1, 3),  # Pass Line wins
    ])
    player = game.add_player()

    wager = Wager(
        game=game,
        player=player,
        definition=defs.PASS_LINE,
        value=25,
    )
    game.place_wager(wager)

    sim = Simulator(game)
    sim.run(2)

    for record in sim.recorder.rolls:
        assert_roll_accounting(record, player.id, 0)

    stats = SessionStatistics(sim.recorder.rolls)

    assert stats.player(player.id).net_profit == 25
    assert stats.wagers.net_resolution_result == 25


# ========================
# BUY BET - VIG ON WIN
# ========================

def test_buy_vig_on_win_reconciliation():
    game = Game(
        settings=GameSettings(
            buy_vig_setting=VigSetting.ON_WIN,
        ),
        predetermined_rolls=[(2, 2)],
    )

    player = game.add_player()

    wager = Wager(
        game=game,
        player=player,
        definition=defs.PLACE_BET,
        value=100,
        target=4,
        _is_buy=True,
    )
    game.place_wager(wager)

    assert wager.is_buy
    assert wager.collected_vig == 0
    assert player.bankroll == 1400

    sim = Simulator(game)
    sim.step()

    record = sim.recorder.rolls[0]
    financials = get_roll_financials(record, player.id)
    outcome = record.wager_outcomes[0]

    assert outcome.resolution is Resolution.WIN
    assert outcome.profit == 195
    assert financials.equity_change == 195
    assert financials.resolution_net == 195
    assert financials.residual == 0

    assert player.bankroll == 1595
    assert wager in game.wagers
    assert wager.collected_vig == 0


# ========================
# BUY BET - UPFRONT VIG
# ========================

def test_buy_upfront_vig_reconciliation():
    game = Game(
        settings=GameSettings(
            buy_vig_setting=VigSetting.UP_FRONT,
        ),
        predetermined_rolls=[(2, 2)],
    )

    player = game.add_player()
    opening_bankroll = player.bankroll

    wager = Wager(
        game=game,
        player=player,
        definition=defs.PLACE_BET,
        value=100,
        target=4,
        _is_buy=True,
    )
    game.place_wager(wager)

    assert opening_bankroll == 1500
    assert wager.collected_vig == 5
    assert player.bankroll == 1395

    sim = Simulator(game)
    sim.step()

    record = sim.recorder.rolls[0]
    financials = get_roll_financials(record, player.id)
    outcome = record.wager_outcomes[0]

    assert outcome.resolution is Resolution.WIN
    assert outcome.profit == 195

    # The engine reports the net winning payout.
    assert financials.equity_change == 195
    assert financials.resolution_net == 195
    assert financials.residual == 0

    assert player.bankroll == 1590
    assert wager.collected_vig == 5
    assert wager in game.wagers


# ========================
# LAY BET - UPFRONT VIG
# ========================

def test_lay_upfront_vig_reconciliation():
    game = Game(predetermined_rolls=[
        (1, 6),  # Lay 4 wins on 7
    ])
    player = game.add_player()

    wager = Wager(
        game=game,
        player=player,
        definition=defs.LAY_BET,
        value=120,
        target=4,
    )
    game.place_wager(wager)

    # $120 Lay 4: $60 gross win, $3 vig
    assert wager.collected_vig == 3
    assert player.bankroll == 1377

    sim = Simulator(game)
    sim.step()

    record = sim.recorder.rolls[0]
    financials = get_roll_financials(record, player.id)
    outcome = record.wager_outcomes[0]

    assert outcome.resolution is Resolution.WIN
    assert outcome.profit == 57

    assert financials.equity_change == 57
    assert financials.resolution_net == 57
    assert financials.residual == 0

    assert player.bankroll == 1434
    assert wager.collected_vig == 3
    assert wager in game.wagers


# ========================
# UNCOMMITTED BUY CANCELLATION
# ========================

def test_uncommitted_buy_cancellation():
    game = Game(
        settings=GameSettings(
            buy_vig_setting=VigSetting.UP_FRONT,
        ),
        predetermined_rolls=[(2, 2)],
    )

    player = game.add_player()
    starting_equity = player.get_equity().total_equity
    starting_bankroll = player.bankroll

    wager = Wager(
        game=game,
        player=player,
        definition=defs.PLACE_BET,
        value=100,
        target=4,
        _is_buy=True,
    )
    game.place_wager(wager)

    assert wager.collected_vig == 5

    # Cancel without rolling.
    game.take_down_wager(wager)

    assert wager not in game.wagers
    assert player.bankroll == starting_bankroll
    assert player.get_equity().total_equity == starting_equity


# ========================
# UNCOMMITTED LAY CANCELLATION
# ========================

def test_uncommitted_lay_cancellation():
    game = Game()
    player = game.add_player()

    starting_equity = player.get_equity().total_equity
    starting_bankroll = player.bankroll

    wager = Wager(
        game=game,
        player=player,
        definition=defs.LAY_BET,
        value=120,
        target=4,
    )
    game.place_wager(wager)

    assert wager.collected_vig == 3

    game.take_down_wager(wager)

    assert wager not in game.wagers
    assert player.bankroll == starting_bankroll
    assert player.get_equity().total_equity == starting_equity


# ========================
# NET COMMITTED BUY ADJUSTMENT
# ========================

def test_upfront_buy_net_adjustment():
    game = Game(
        settings=GameSettings(
            buy_vig_setting=VigSetting.UP_FRONT,
        ),
        predetermined_rolls=[(2, 2)],
    )
    player = game.add_player()

    wager = Wager(
        game=game,
        player=player,
        definition=defs.PLACE_BET,
        value=100,
        target=4,
        _is_buy=True,
    )
    game.place_wager(wager)

    sim = Simulator(game)
    sim.step()

    # $100 -> $200 -> $150 before next roll.
    game.increase_wager(wager, 100)
    game.decrease_wager(wager, 50)

    assert wager.value == 150

    expected_vig = game.calculate_vig(wager)
    assert wager.collected_vig == expected_vig

    sim.step()

    record = sim.recorder.rolls[1]
    changes = record.wager_changes_before

    assert len(changes) == 1

    change = changes[0]

    assert change.change_type is WagerChangeType.ADJUST
    assert change.value_change == 50
    assert change.vig_change == expected_vig - 5
    assert change.before.value == 100
    assert change.after.value == 150

    # No wager resolution, so no roll-generated P/L.
    assert_roll_accounting(record, player.id, 0)


# ========================
# PERSISTENT LAY WINS
# ========================

def test_lay_two_wins_same_wager():
    game = Game(predetermined_rolls=[
        (1, 6),  # Lay 4 wins
        (2, 5),  # Lay 4 wins again
    ])
    player = game.add_player()

    wager = Wager(
        game=game,
        player=player,
        definition=defs.LAY_BET,
        value=120,
        target=4,
    )
    game.place_wager(wager)

    original_id = wager.id

    sim = Simulator(game)
    sim.run(2)

    records = sim.recorder.rolls

    assert len(records) == 2

    for record in records:
        outcome = record.wager_outcomes[0]

        assert outcome.wager_id == original_id
        assert outcome.resolution is Resolution.WIN
        assert outcome.profit == 57

        assert_roll_accounting(record, player.id, 0)

    # Initial placement only.
    assert len(records[0].wager_changes_before) == 1
    assert (
        records[0].wager_changes_before[0].change_type
        is WagerChangeType.PLACE
    )

    # The wager won but stayed on the table.
    assert records[1].wager_changes_before == ()

    assert wager.id == original_id
    assert wager in game.wagers
    assert player.bankroll == 1491