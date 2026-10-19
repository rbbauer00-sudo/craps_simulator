# Craps Simulator

A modular Python craps simulator built around a rule-driven game engine, a deterministic simulation controller, and a statistics and session-recording system.

**Current milestone:** Statistics v1.0 — the engine, simulation framework, core statistics, and session financial reporting are implemented and tested. A Pygame interface is planned next.

## Features

### Game engine

- Craps gameplay with Pass Line, Don't Pass, Come, Don't Come, odds, Place, Buy, Lay, Field, hardways, hops, proposition bets, ATS, and Fire bets.
- Wager validation, contract restrictions, working/off state, payouts, and bankroll accounting.
- Configurable game rules, including Buy/Lay vig behavior.
- Multiple players, shooter rotation, and deterministic dice rolls for testing.
- Stable wager IDs for tracking bets that persist through multiple rolls.

### Simulation

- Single-step or multi-roll simulations using `Simulator`.
- Pluggable strategies with hooks before and after each roll.
- A reference `PassLineStrategy`.
- The game engine remains independent of the simulator and future UI.

### Statistics and recording

- **Dice:** roll totals, combinations, and expected frequencies.
- **Shooters:** hand lengths, seven-outs, points established and made, and per-shooter results.
- **Players:** bankroll, total and liquid equity, profit/loss, equity curves, and drawdowns.
- **Wagers:** resolutions, winning payouts, lost stakes, and wager exposure.
- **Sessions:** immutable per-roll records, opening and closing snapshots, and per-player financial summaries.

Wager changes follow a **commit-on-roll** model: only the net wager state at the start of a roll is committed to the historical record. Intermediate UI changes (for example, increasing a bet and then partially reversing it before rolling) do not create artificial betting activity.

## Requirements

- Python **3.12 or later**
- `pip`
- `pytest` for development and testing

## Installation

Clone the repository and install it in editable mode:

```bash
git clone <YOUR_REPOSITORY_URL>
cd craps_simulator

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -e ".[dev]"
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.

The distribution is named `craps-engine`; the importable packages are `engine` and `simulator`.

## Quick start

### Run the example simulation

```bash
python main.py
```

The example creates a game, adds a player, applies `PassLineStrategy`, and runs 1,000 rolls.

### Run a deterministic session

```python
from engine import Game, Wager, defs
from simulator import Simulator
from simulator.statistics import SessionStatistics

game = Game(predetermined_rolls=[(2, 2), (1, 3)])
player = game.add_player()

# Create the simulator before session betting starts so it
# records the player's opening equity.
sim = Simulator(game)

wager = Wager(
    game=game,
    player=player,
    definition=defs.PASS_LINE,
    value=25,
)
game.place_wager(wager)

sim.run(2)
sim.close()

stats = SessionStatistics(
    sim.recorder.rolls,
    opening_players=sim.recorder.opening_players,
    closing_players=sim.recorder.closing_players or (),
    closing_wagers=sim.recorder.closing_wagers or (),
)

print("Rolls:", stats.roll_count)
print("Sevens:", stats.dice.seven_count)
print("Completed shooter hands:", stats.shooters.completed_hands)
print("Net equity change:", stats.player(player.id).net_profit)

summary = stats.financial_summary(player.id)
print("Opening equity:", summary.opening_equity)
print("Closing equity:", summary.closing_equity)
print("Outstanding wager value:", summary.outstanding_wager_value)
```

`SessionStatistics` analyzes a **snapshot** of recorded data. Construct a new instance after additional rolls if you want updated results. A closed session cannot accept further rolls through that simulator.

## Financial accounting notes

The simulator distinguishes several financial measurements:

| Measurement | Meaning |
| --- | --- |
| Bankroll | Cash currently available for wagering |
| Total equity | Cash plus equity represented by outstanding wagers |
| Liquid equity | Cash plus removable wager principal |
| Reserved equity | Wager principal restricted by contracts |
| Net equity change | Closing equity minus opening equity |
| Net resolution result | Winning payout profit minus lost wager stakes |

**Net equity change is not always net gambling profit.** External deposits and withdrawals can affect it, while refundable up-front vig and outstanding positions can complicate reconciliation. `net_resolution_result` is also not a complete transaction ledger.

Opening snapshots are recorded when `Simulator` is created; closing snapshots are recorded by `sim.close()`. Closing a session **does not** settle or remove open wagers.

A complete financial summary requires opening and closing snapshots for the player. Players joining after session opening are supported in roll-based analysis, but their complete-session financial summary needs an explicit entry baseline in a future version.

## Project layout

```text
craps_simulator/
├── engine/                  # Game rules, dice, players, wagers
├── simulator/
│   ├── simulator.py         # Roll execution and strategy integration
│   ├── strategy.py          # Strategy interface
│   ├── strategies/          # Betting strategies
│   └── statistics/          # Records, analyzers, financial summaries
├── tests/                   # Pytest unit and integration tests
├── assets/                  # Images and other project assets
├── main.py                  # Command-line example
├── pyproject.toml           # Packaging and pytest configuration
└── README.md
```

The planned `ui/` package will contain the Pygame application and presentation layer.

## Testing

Run all tests from the project root:

```bash
python -m pytest
```

Run an individual file:

```bash
python -m pytest tests/test_session_closing.py -v
```

Run the core statistics and financial integration tests as part of the full suite. Test scenarios cover deterministic payouts, wager lifecycle and identity, contract behavior, Buy/Lay vig, net committed wager adjustments, shooter rotation, and opening/closing snapshots.

## Milestones

- **Engine v1.0:** Core gameplay and wager rules.
- **Statistics v1.0:** Simulation, immutable session recording, core analyzers, financial reconciliation tests, and session financial summaries.
- **Next — Pygame UI v0.1:** Game window, table rendering, input, betting controls, and live statistics.

Future enhancements may include Monte Carlo aggregation, strategy comparisons, detailed cash-flow events, session replay, and richer analytics.

## Development principles

- The **engine** is authoritative for game rules, payouts, and bankroll operations.
- The **simulator** orchestrates rolls and strategies.
- The **recorder** preserves immutable historical observations.
- The **statistics layer** derives results rather than duplicating game rules.
- The **UI** will use the engine's public methods and will not implement its own betting logic.

## License

No license has been specified yet. Add a `LICENSE` file if you intend to define distribution or reuse terms.
