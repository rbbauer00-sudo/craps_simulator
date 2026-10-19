from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING
from .exceptions import InsufficientFundsError
if TYPE_CHECKING:
    from .wager import Wager
    from .game import Game


@dataclass(frozen=True)
class PlayerResult:
    name: str
    final_bankroll: int
    forfeited_value: int


@dataclass(frozen=True)
class PlayerEquity:
    bankroll: int
    removable_equity: int
    reserved_equity: int
    total_equity: int

    @property
    def liquid_equity(self) -> int:
        return self.bankroll + self.removable_equity


class Player:

    def __init__(
        self,
        game: Game, 
        name: str,
        bankroll: int,
        player_id: int | None = None

    ) -> None:
        
        self._game = game
        self._id = player_id
        self._bankroll = bankroll
        self._name = name

    @property
    def id(self) -> int:
        return self._id

    @property
    def position(self) -> int:
        return self.game.players.index(self)

    @property
    def game(self) -> Game:
        return self._game

    @property
    def name(self) -> str:
        return self._name

    @property
    def bankroll(self):
        return self._bankroll

    @property
    def contracted_funds(self) -> int:
        return sum(
            wager.contract_min or 0
            for wager in self.get_wagers()
        )


    @property
    def funds_on_table(self) -> int:
        return sum(
            wager.value
            for wager in self.get_wagers()
        )


    @property
    def removable_funds(self) -> int:
        return self.funds_on_table - self.contracted_funds


    @property
    def removable_equity(self) -> int:
        return self._bankroll + self.removable_funds

    
    def withdraw(self, amt: int) -> None:

        if type(amt) is not int or amt < 0:
            raise ValueError(
                "Withdrawal amount must be a nonnegative integer; "
                f"received {amt!r}."
            )

        if amt > self.bankroll:
            raise InsufficientFundsError(
                f"Insufficient funds. You need ${amt}, "
                f"but only have ${self.bankroll} available."
            )

        self._bankroll -= amt


    def deposit(self, amt: int) -> None:
        
        if type(amt) is not int or amt < 0:
            raise ValueError(
                "Deposit amount must be a nonnegative integer; "
                f"received {amt!r}."
            )
        
        self._bankroll += amt


    def set_bankroll(self, amt) -> None:
        if type(amt) is not int or amt < 0:
            raise ValueError(
                "Player bankroll must be a nonnegative integer; "
                f"received {amt!r}."
            )

        self._bankroll = amt


    def get_wagers(self) -> list[Wager]:
        wager_list = self.game.wagers

        return [
            wager for wager in wager_list 
            if wager.player is self
        ]


    def get_equity(self) -> PlayerEquity:
        wagers = self.get_wagers()

        reserved = sum(
            wager.contract_min or 0
            for wager in wagers
        )

        total = (
            self.bankroll
            + sum(wager.value for wager in wagers)
        )

        removable = total - self.bankroll - reserved

        return PlayerEquity(
            bankroll=self.bankroll,
            removable_equity=removable,
            reserved_equity=reserved,
            total_equity=total,
        )


    def __repr__(self):
        return f'Player Obj: {self.name}'


    def __str__(self):
        return self.name
    
    