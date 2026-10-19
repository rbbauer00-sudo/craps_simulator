from __future__ import annotations
from typing import TYPE_CHECKING
from .wager import Wager, WagerResult
from .player import Player, PlayerResult
from .dice import Dice, RollResult
from .enums import Resolution, WagerType, VigSetting
from .exceptions import GameRuleViolation, EngineStateError
from . import constants as const
from dataclasses import dataclass
if TYPE_CHECKING:
    from .dice import RollResult

@dataclass(frozen=True)
class GameRollResult:
    roll: RollResult
    wager_results: tuple[WagerResult, ...]

    point_before: int | None
    point_after: int | None
    
    shooter_id: int | None
    shooter_roll_count: int
    seven_out: bool


@dataclass(frozen=True)
class GameSettings:
    field_3x_on_12: bool = True
    buy_vig_setting: VigSetting = VigSetting.AUTO_BUY
    auto_buy_level: int = 20
    allow_put_bets: bool = True


class Game:
    def __init__(
            self,
            settings: GameSettings | None = None,
            seed: int | str | None = None,
            predetermined_rolls: list[
                int | tuple[int,int] | RollResult
            ] | None = None,
    ) -> None:
        self._wagers: list[Wager] = []
        self._players: list[Player] = []
        self._point: int | None = None
        self._dice = Dice(
            seed=seed,
            predetermined_rolls=predetermined_rolls,
        )
        self._settings = (
            settings 
            if settings is not None 
            else GameSettings()
        )

        self._shooter_roll_count: int = 0
        self._shooter: Player | None = None
        self._next_player_id: int = 0
        self._next_wager_id: int = 0

    @property
    def settings(self) -> GameSettings:
        return self._settings

    @property
    def wagers(self) -> tuple[Wager, ...]:
        return tuple(self._wagers)

    @property
    def players(self) -> tuple[Player, ...]:
        return tuple(self._players)

    @property
    def point(self) -> int | None:
        return self._point

    @property
    def shooter_roll_count(self) -> int:
        return self._shooter_roll_count

    @property
    def dice(self):
        return self._dice


    def reset(
        self,
        settings: GameSettings | None = None,
        seed: int | str | None = None,
        predetermined_rolls: list[
            int | tuple[int,int] | RollResult
        ] | None = None,
    ) -> None:

        """
        Return game to initial state.  Removes all
        current players and wagers.  Shooter roll
        count is reset to zero and shooter index
        is reset to None.  Player ID and Wager ID
        are preserved to avoid duplicate identifiers
        between sessions.
        """
        
        new_dice = Dice(
            seed=seed,
            predetermined_rolls=predetermined_rolls,
        )

        new_settings = (
            settings 
            if settings is not None
            else self.settings
        )

        self._wagers.clear()
        self._players.clear()
        self._point = None
        self._shooter_roll_count = 0
        self._shooter = None

        self._dice = new_dice
        self._settings = new_settings

    @property
    def shooter(self) -> Player | None:
        return self._shooter

    def _advance_shooter(self) -> Player | None:
        if not self.players:
            self._shooter = None
            return None

        elif self._shooter not in self.players:
            self._shooter = self.players[0]
            return self._shooter

        current_index = self.players.index(self._shooter)
        next_index = (current_index + 1) % len(self.players)
       
        self._shooter = self.players[next_index]
        return self._shooter

    def add_player(
        self,
        name: str | None = None,
        bankroll: int = 1500,
    ) -> Player:
        """
        Create a new player object with
        unique ID.  Returns newly created
        player.
        """
        
        player_id = self._next_player_id
        self._next_player_id += 1
        
        player = Player(
            game=self,
            name=name or f"Player {player_id}",
            bankroll=bankroll,
            player_id=player_id,
        )

        self._players.append(player)
        if self.shooter is None:
            self._advance_shooter()
        return player


    def remove_player(self, player: Player) -> PlayerResult:

        # Verify player is active
        if player not in self.players:
            raise ValueError(
                "Cannot remove unregistered "
                f"player: {player}."
            )

        # Record previous shooter index
        old_index = (
            self._players.index(player)
            if player is self._shooter
            else None
        )

        # Take down odds wagers first
        for wager in player.get_wagers().copy():
            if (
                wager.definition.wager_type in(
                    WagerType.LAY_ODDS,
                    WagerType.LINE_ODDS,
                )
            ):
                self.take_down_wager(wager)

        # Take down any remaining refundable wagers
        for wager in player.get_wagers().copy():
            if not wager.contract_min:
                self.take_down_wager(wager)

        # Refund any uncontracted value
        for wager in player.get_wagers():
            if (
                wager.contract_min is not None
                and wager.value > wager.contract_min
            ):
                self.decrease_wager(
                    wager,
                    wager.value - wager.contract_min,
                )

        # Record player data and remove player from game
        result = PlayerResult(
            name=player.name,
            final_bankroll=player.bankroll,
            forfeited_value=player.funds_on_table,
        )

        # Forfeit contracted wagers
        for wager in player.get_wagers():
                self._wagers.remove(wager)

        # Remove player
        self._players.remove(player)

        # Update shooter reference
        if not self._players:
            self._shooter = None
        elif old_index is not None:
            next_index = old_index % len(self._players)
            self._shooter = self._players[next_index]

        return result


    def place_wager(
        self,
        wager: Wager,
    ) -> None:

        # Verify game object reference
        if wager.game is not self:
            raise ValueError(
                "Incorrect reference to game object."
            )

        # Verify amount is positive integer
        if type(wager.value) is not int or wager.value <= 0:
            raise ValueError(
                f"unexpected amount: {wager.value}. Placement "
                "amount must be greater than zero."
            )

        # Verify player is active
        if wager.player not in self.players:
            raise ValueError(
                f"Player {wager.player} is not an "
                "active player in game.players."
            )

        # Verify unique wager ID
        if wager.id is not None:
            raise ValueError(
                f"Wager {wager.id} has already been placed."
            )

        # Verify wager-specific placement rule(s)
        wager.definition.placement_rule(wager)
        
        # Charge vig to player, if applicable
        wager_type = wager.definition.wager_type
        up_front_vig = (
            self.calculate_vig(wager) 
            if (
                wager_type is WagerType.LAY_BET
                or (
                    self.settings.buy_vig_setting == 
                        VigSetting.UP_FRONT
                    and wager_type is WagerType.PLACE_BET
                )
            ) else 0
        )

        # Withdraw player funds
        wager.player.withdraw(wager.value + up_front_vig)
        wager.collected_vig += up_front_vig

        # Assign unique wager ID and add to wager list
        wager._id = self._next_wager_id
        self._next_wager_id += 1
        self._wagers.append(wager)


    def increase_wager(
        self,
        wager: Wager,
        amount: int,
    ) -> None:
        """
        Increase the value of a wager and deduct the
        cost from the player's bankroll.  Raises error
        if player cannot cover the increase or the vig
        """

        if wager not in self.wagers:
            raise GameRuleViolation(
                "Cannot increase an inactive wager."
            )

        if type(amount) is not int or amount <= 0:
            raise ValueError(
                f"unexpected amount: {amount}. Increase "
                "amount must be greater than zero."
            )

        new_value = wager.value + amount

        if (
            wager.contract_max is not None
            and new_value > wager.contract_max
        ):
            raise GameRuleViolation(
                f"{wager.definition.name} cannot exceed "
                F"its contract maximum of "
                f"${wager.contract_max}."
            )

        # Charge vig to player
        wager_type = wager.definition.wager_type

        new_up_front_vig = (
            self.calculate_vig(wager, new_value) 
            if (
                wager_type is WagerType.LAY_BET
                or (
                    self.settings.buy_vig_setting == 
                        VigSetting.UP_FRONT
                    and wager_type is WagerType.PLACE_BET
                )
            ) else 0
        )

        vig_due = new_up_front_vig - wager.collected_vig

        wager.player.withdraw(amount + vig_due)
        wager.collected_vig += vig_due

        wager.value = new_value


    def decrease_wager(
        self,
        wager: Wager,
        amount: int,
    ) -> None:

        if wager not in self.wagers:
            raise GameRuleViolation(
            "Cannot decrease an inactive wager."
        )

        if type(amount) is not int or amount <= 0:
            raise ValueError(
                f"unexpected amount: {amount}. Decrease "
                "amount must be greater than zero."
            )

        new_value = wager.value - amount

        if new_value < 0:
            raise GameRuleViolation(
                f"You cannot decrease this wager by ${amount}. "
                f"The wager is only ${wager.value}."
            )

        if new_value == 0:
            return self.take_down_wager(wager)

        if (
            wager.contract_min is not None
            and new_value < wager.contract_min
        ):
            raise GameRuleViolation(
                f"{wager.definition.name} cannot be below "
                f"its contract minimum of "
                f"${wager.contract_min}."
            )


        # Refund collected vig
        wager_type = wager.definition.wager_type
        
        new_up_front_vig = (
            self.calculate_vig(wager, new_value) 
            if (
                wager_type is WagerType.LAY_BET
                or (
                    self.settings.buy_vig_setting == 
                        VigSetting.UP_FRONT
                    and wager_type is WagerType.PLACE_BET
                )
            ) else 0
        )

        vig_refund = wager.collected_vig - new_up_front_vig

        wager.player.deposit(amount + vig_refund)
        wager.collected_vig -= vig_refund

        wager.value = new_value


    def take_down_wager(
        self, 
        wager: Wager,
    ) -> None:
        """
        Voluntary removal of an active wager by the 
        player.  Triggers removal of any active odds
        wagers associated with wager, regardless of
        working status, to be removed.  Honors wager
        contracts and raises GameRuleViolation if 
        removal of contracted wager is attempted.
        """

        if wager not in self.wagers:
            raise GameRuleViolation(
                "Cannot take down an inactive wager."
            )

        if (
            wager.contract_min is not None
            and wager.contract_min > 0
        ):
            raise GameRuleViolation(
                f"{wager.definition.name} cannot be taken down "
                "while contracted."
            )
       
        child = self.get_child_wager(wager)
        
        if child is not None:
            self._refund_wager(child)
            
        self._refund_wager(wager)

    def _refund_wager(
        self,
        wager: Wager,
    ) -> None:

        """
        Private method for removal of wagers
        after a WIN result or for removal of
        orphaned non-working odds wagers when 
        the parent wager is resolved by WIN or
        LOSS.  Ignores contracts but does not
        cascade removal of linked odds wagers.
        When an odds wager is working, 
        it will recieve its own direct resolution 
        call from get_result() upon resolution of 
        the parent wager to avoid a potential 
        double refund bug.
        """

        if wager not in self.wagers:
            raise EngineStateError(
                "Cannot refund inactive wager: "
                f"{wager.definition.name}."
            )

        wager.player.deposit(
            wager.value + wager.collected_vig
        )

        self._wagers.remove(wager)


    @staticmethod
    def calculate_vig(wager: Wager, new_value: int | None = None):
        """
        Returns the vig charged on a wager of a specified value.
        Uses wager current value if new_value is not specified.
        Returns a minimum of 1 for place and lay bets.
        For buy bets, vig is based on the wager value itself.
        For lay bets, vig is based on the expected profit.
        All other bet types, including regular place bets, return 0.
        """

        wager_value = (
            wager.value
            if new_value is None
            else new_value
        )

        wager_type = wager.definition.wager_type

        if wager_type is WagerType.LAY_BET:
            
            match wager.target:
                case 4 | 10:
                    n, d = (1, 2)

                case 5 | 9:
                    n, d = (2, 3)

                case 6 | 8:
                    n, d = (5, 6)

                case _:
                    raise EngineStateError(
                        f"Invalid Lay target: {wager.target}"
                    )
                
            vig_basis = wager_value * n // d
        
        elif (
            wager_type is WagerType.PLACE_BET
            and wager.is_buy
        ):
            vig_basis = wager_value

        else:
            vig_basis = 0

        return (
            max(1, round((vig_basis * 0.05)))
            if vig_basis
            else 0
        )


    def set_wager_buy_status(
        self, 
        wager: Wager,
        new_status: bool,
    ) -> None:
        """
        Toggles buy status of PLACE wager
        and handles vig accounting.
        Raises error if attempted on any
        other wager type.
        """
        if wager not in self.wagers:
            raise GameRuleViolation(
                "Cannot modify an inactive wager."
            )

        old_status = wager._is_buy

        wager.is_buy = new_status

        if self.settings.buy_vig_setting is VigSetting.UP_FRONT:
            new_vig = self.calculate_vig(wager)
            delta_vig = new_vig - wager.collected_vig

            try:
                if delta_vig > 0:
                    wager.player.withdraw(delta_vig)
                elif delta_vig < 0:
                    wager.player.deposit(-delta_vig)

            except Exception:
                wager._is_buy = old_status
                raise

            wager.collected_vig = new_vig


    def set_wager_working_status(
        self,
        wager: Wager,
        new_status: bool,
    ) -> None:
        """
        Sets the working status of a wager.  
        Raises error if unsuccessful.
        """

        if wager not in self.wagers:
            raise GameRuleViolation(
                "Cannot modify an inactive wager."
            )


        wager.is_working = new_status

     
    def get_wager(
        self,
        player: Player,
        wager_type: WagerType,
        target: int | tuple[int, int] | None = None,
    ) -> Wager | None:
        """
        Search for a wager object by type,
        target, and player.  Returns None if
        not found.
        """

        for wager in self.wagers:

            if (
                wager.definition.wager_type
                is wager_type
                and wager.target == target
                and wager.player is player
            ):
                return wager
        
        return None


    def get_child_wager(
        self,
        parent_wager: Wager,
    ) -> Wager | None:
        """
        Returns the associated odds wager for
        a pass/don't pass bet.  Returns None 
        if odds wager nonexistent/nonapplicable.
        """

        children = [
            wager for wager in self.wagers
            if wager.parent_wager is parent_wager
        ]

        if len(children) > 1:
            raise EngineStateError(
                "Multiple child wagers found for parent "
                f"{parent_wager.definition.wager_type.name}: "
                f"expected at most one, found {len(children)}."
            )

        return children[0] if children else None


    def roll(
        self, 
        d1: int | None = None, 
        d2: int | None = None,
    ) -> GameRollResult:

        point_before = self.point

        shooter_id = (
            self.shooter.id
            if self.shooter is not None
            else None
        )

        roll = self._dice.roll(d1, d2)
        self._shooter_roll_count += 1

        completed_shooter_roll_count = self.shooter_roll_count

        results = self._get_all_wager_results(roll)
        self._validate_roll_results(results)
        self._execute_all_wager_results(results)

        self._update_point(roll)
        self._refresh_contracts()

        return GameRollResult(
            roll=roll,
            wager_results=tuple(results),
            point_before=point_before,
            point_after=self.point,
            shooter_id=shooter_id,
            shooter_roll_count=completed_shooter_roll_count,
            seven_out=(
                point_before is not None
                and roll.total == 7
            ),
        )


    def get_last_roll(self) -> RollResult | None:
        return self._dice.get_last_roll()


    def get_roll_history(self) -> tuple[RollResult, ...]:
        return self._dice.get_history()


    def _update_point(
            self, 
            roll: RollResult,
        ) -> None:

        roll_total = roll.total

        # Point Hit
        if self.point is not None:
            if roll_total == self.point:
                self._point = None

            # Seven Out
            elif roll_total ==7:
                self._point = None
                self._shooter_roll_count = 0
                self._advance_shooter()

        # Point Established
        elif roll_total in {4,5,6,8,9,10}:
            self._point = roll_total


    def _get_single_wager_result(
        self,
        wager: Wager,
        roll: RollResult,
    ) -> WagerResult:

        resolution = wager.definition.resolution_rule(
            wager,
            roll,
        )

        profit = (
            wager.definition.payout_rule(wager) 
            if resolution is Resolution.WIN 
            else 0
        )

        move_to = (
            roll.total
            if resolution is Resolution.MOVE 
            else None
        )
        
        return WagerResult(
            wager=wager,
            resolution=resolution,
            profit=profit,
            move_to=move_to,
        )
    
    
    def _get_all_wager_results(
        self,
        roll: RollResult,
    ) -> list[WagerResult]:

        return [
            self._get_single_wager_result(
                wager, 
                roll,
            ) 
            for wager in self.wagers
        ]


    def _validate_roll_results(
        self,
        results: list[WagerResult],
    ) -> None:

        if len(results) != len(self.wagers):
            raise EngineStateError(
                "Roll result count mismatch: "
                f"{len(results)} results for "
                f"{len(self.wagers)} active wagers."
            )

        seen = set()

        for result in results:

            if not isinstance(result, WagerResult):
                raise EngineStateError(
                    "Unexpected result type: "
                    f"{type(result).__name__}: {result!r}."
                )
            
            wager = result.wager
            
            if wager not in self.wagers:
                raise EngineStateError(
                    "Roll resolution references an inactive "
                    f"wager: {wager.definition.name}."
                )

            if wager in seen:
                raise EngineStateError(
                    "Duplicate roll result for wager: "
                    f"{wager.definition.name}."
                )

            seen.add(wager)

            if not isinstance(result.resolution, Resolution):
                raise EngineStateError(
                    f"Invalid resolution {result.resolution!r} "
                    f"for {wager.definition.name}."
                )

            if type(result.profit) is not int or result.profit <0:
                raise EngineStateError(
                    f"Invalid profit {result.profit!r} "
                    f"for {wager.definition.name}."
                )

            if result.resolution is Resolution.MOVE:
                if result.move_to not in const.BOX_NUMS:
                    raise EngineStateError(
                        f"Invalid MOVE destination: "
                        f"{result.move_to!r}."
                    )

            elif result.move_to is not None:
                raise EngineStateError(
                    f"Unexpected move destination "
                    f"{result.move_to!r} for "
                    f"{result.resolution.name} result."
                )

            
            
    def _execute_single_wager_result(
        self, 
        wager_result:WagerResult
    ) -> None:

        match wager_result.resolution:
            case Resolution.WIN:
                return self._handle_win(
                    wager_result,
                )

            case Resolution.LOSE:
                return self._handle_loss(
                    wager_result,
                )
            
            case Resolution.PUSH:
                return self._handle_push(
                    wager_result,
                )
            
            case Resolution.MOVE:
                return self._handle_move(
                    wager_result,
                )
            
            case Resolution.REMOVE:
                return self._handle_remove(
                    wager_result,
                )
            
            case Resolution.NONE:
                return None

            
    def _execute_all_wager_results(
        self,
        results: list[WagerResult],
    ) -> None:

        for result in results:
            self._execute_single_wager_result(result)


    def _handle_win(
        self, 
        wager_result: WagerResult,
    ) -> None:
        """
        All wagers in engine stay up by default after 
        a win except for come bets, odds bets, and any 
        other bet that would break game rules by staying 
        up.  UI and simulators can be set to automtically
        take these bets down without penalty.  For wagers 
        where up front vig applies, the vig will 
        automatically be deducted from winnings and the 
        new wager will start with the correct accounting 
        for collected_vig.
        """

        # Reset collected_vig
        wager = wager_result.wager
        wager_type = wager.definition.wager_type
        vig_setting = self.settings.buy_vig_setting

        wager.collected_vig = (
            self.calculate_vig(wager)
        ) if (
            wager_type is WagerType.LAY_BET
            or (
                wager_type is WagerType.PLACE_BET
                and wager.is_buy
                and vig_setting is VigSetting.UP_FRONT
            )
        ) else 0
    
        wager.player.deposit(
            wager_result.profit
        )

        if wager.definition.remove_after_win:
            self._refund_wager(
                wager)


    def _handle_loss(
        self, 
        wager_result: WagerResult,
    ) -> None:
        """
        Wager is removed from game and
        player inventories without
        refunding player.  Any up front vig
        that has been collected will not be
        refunded.  Wager objects are not
        intended to be reused after loss so
        resetting collected_vig should not
        be necessary.
        """

        wager = wager_result.wager

        if wager not in self._wagers:
            raise EngineStateError(
                "Attempted to resolve a loss for an "
                f"inactive wager: {wager.definition.name}."
            )
        
        self._wagers.remove(
            wager
        )


    def _handle_remove(
            self,
            wager_result: WagerResult
    ) -> None:
        """
        Marks orphaned odds wagers that are
        not working when the parent is
        resolved for removal.  Wager value is
        refunded to player.
        """

        wager = wager_result.wager
        self._refund_wager(wager)    


    def _handle_push(
        self, 
        _wager_result: WagerResult,
    ) -> None:
        """
        Essentially a no-op function in engine.
        May become useful for UI/Sim implementation.
        """
        pass


    def _handle_move(
        self, 
        wager_result: WagerResult,
    ) -> None:
        """
        Move come/don't come bets to a
        point after establishment.
        """

        wager = wager_result.wager
        wager.target = wager_result.move_to


    def _refresh_contracts(self) -> None:
        """
        Update contract limits for all 
        active wagers after a roll.
        """
        
        for wager in self.wagers:
            wager.definition.contract_rule(
                wager,
            )

