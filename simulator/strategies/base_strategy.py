
from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .strategy_context import StrategyContext


class Strategy(ABC):

    def on_activate(self, ctx: "StrategyContext") -> None:
        pass

    def on_deactivate(self, ctx: "StrategyContext") -> None:
        pass

    def before_roll(self, ctx: "StrategyContext") -> None:
        pass

    def after_roll(self, ctx: "StrategyContext") -> None:
        pass