
from __future__ import annotations

from typing import TYPE_CHECKING

from engine import Resolution, Wager
from .animation_settings import AnimationSettings, AnimationMode
from ui.game_elements import ChipSprite, WagerSprite

if TYPE_CHECKING:
    from ui.states.playing_state import PlayingState


class WagerAnimationController:
    

    def __init__(
        self, 
        state: PlayingState,
        settings: AnimationSettings,
    ) -> None:
        
        self.state = state
        self.settings = settings

        self.resolving_sprites: list[WagerSprite] = []
        self.returning_wagers: list[WagerSprite] = []
        self.moving_wagers: list[WagerSprite] = []
        self.payout_sprites: list[ChipSprite] = []

        self.removing_wagers: list[WagerSprite] = []
        self.refunding_vig_chips: list[ChipSprite] = []

        self.adjustment_chips: list[ChipSprite] = []
        self.adjusting_vig: set[Wager] = set()
        self.adjustment_refund_pending = False

        self.renewal_payouts: list[
            tuple[ChipSprite, int, Wager]
        ] = []
        self.renewal_vig_chips: list[ChipSprite] = []
        self.renewing_vig: set[Wager] = set()

        self.placing_wagers: list[WagerSprite] = []
        self.placing_vig_chips: dict[Wager, ChipSprite] = {}

        self.payout_stage = "idle"


    @property
    def is_animating(self) -> bool:
        return (
            self.payout_stage != "idle"
            or bool(self.placing_wagers)
            or bool(self.placing_vig_chips)
            or bool(self.removing_wagers)
            or bool(self.refunding_vig_chips)
            or bool(self.adjustment_chips)
        )


    def travel_duration(self) -> float:
        return self.settings.duration(0.4)


    def payout_hold(self) -> float:
        return self.settings.duration(0.35)


    def start(self) -> None:
        match self.settings.mode:
            case AnimationMode.FULL:
                self.start_full()

            case AnimationMode.SIMULTANEOUS:
                self.start_simultaneous()

            case AnimationMode.MINIMAL | AnimationMode.INSTANT:
                raise NotImplementedError(
                    f"{self.settings.mode.name} mode "
                    "is not implemented yet."
                )


    def start_full(self) -> None:
        state = self.state

        if state.current_roll is None:
            raise RuntimeError("No current roll to resolve.")

        self.reset_resolution()

        active_wagers = set(state.engine.wagers)
        self.payout_stage = "arriving"

        for result in state.current_roll.wager_results:
            sprite = state.wager_sprites.get(result.wager)

            if sprite is None:
                continue

            match result.resolution:
                case Resolution.LOSE:
                    sprite.move_to(
                        state.dealer_position,
                        duration=self.travel_duration(),
                    )
                    self.resolving_sprites.append(sprite)

                case Resolution.WIN:
                    wager = result.wager

                    if wager not in active_wagers:
                        self.returning_wagers.append(sprite)

                    vig = state.winning_vig_for(wager)
                    gross_profit = result.profit + vig

                    if vig > 0:
                        self.renewing_vig.add(wager)

                    if gross_profit <= 0:
                        continue

                    x, y = sprite.rect.center

                    payout = ChipSprite(
                        gross_profit,
                        state.dealer_position,
                        state.visible_sprites,
                    )

                    payout.move_to(
                        (x + 55, y),
                        duration=self.travel_duration(),
                        hold=self.payout_hold(),
                    )

                    self.payout_sprites.append(payout)

                    if vig > 0:
                        self.renewal_payouts.append(
                            (payout, result.profit, wager)
                        )

                case Resolution.MOVE:
                    target = result.move_to

                    if target not in state.COME_POSITIONS:
                        raise ValueError(
                            f"No Come position defined for {target}"
                        )

                    sprite.move_to(
                        state.COME_POSITIONS[target],
                        duration=self.travel_duration(),
                    )
                    self.moving_wagers.append(sprite)

                case Resolution.REMOVE:
                    self.returning_wagers.append(sprite)

                case Resolution.PUSH | Resolution.NONE:
                    pass

                case _:
                    raise ValueError(
                        f"Unhandled resolution: {result.resolution}"
                    )


    def start_simultaneous(self) -> None:
        state = self.state

        if state.current_roll is None:
            raise RuntimeError("No current roll to resolve.")

        self.reset_resolution()
        self.payout_stage = "simultaneous"

        active_wagers = set(state.engine.wagers)
        player_position = state.player_sprite.rect.center
        duration = self.travel_duration()

        for result in state.current_roll.wager_results:
            sprite = state.wager_sprites.get(result.wager)

            if sprite is None:
                continue

            match result.resolution:

                case Resolution.LOSE:
                    sprite.move_to(
                        state.dealer_position,
                        duration=duration,
                    )
                    self.resolving_sprites.append(sprite)

                case Resolution.WIN:
                    wager = result.wager

                    # Return principal if the engine
                    # has removed the winning wager.
                    if wager not in active_wagers:
                        sprite.move_to(
                            player_position,
                            duration=duration,
                        )
                        self.returning_wagers.append(sprite)

                    vig = state.winning_vig_for(wager)

                    if vig > 0:
                        self.renewing_vig.add(wager)

                    # The engine has already calculated
                    # the player's net profit.
                    if result.profit > 0:
                        x, y = sprite.rect.center

                        payout = ChipSprite(
                            result.profit,
                            (x + 55, y),
                            state.visible_sprites,
                        )

                        payout.move_to(
                            player_position,
                            duration=duration,
                        )

                        self.payout_sprites.append(payout)

                    # Commission is collected separately,
                    # starting beside the winning wager.
                    if vig > 0:
                        x, y = sprite.rect.center

                        commission = ChipSprite(
                            vig,
                            (x + 55, y),
                            state.visible_sprites,
                            radius=14,
                            color=(180, 130, 45),
                        )

                        commission.move_to(
                            state.dealer_position,
                            duration=duration,
                        )

                        self.renewal_vig_chips.append(
                            commission
                        )

                case Resolution.MOVE:
                    target = result.move_to

                    if target not in state.COME_POSITIONS:
                        raise ValueError(
                            f"No Come position defined for {target}"
                        )

                    sprite.move_to(
                        state.COME_POSITIONS[target],
                        duration=duration,
                    )

                    self.moving_wagers.append(sprite)

                case Resolution.REMOVE:
                    sprite.move_to(
                        player_position,
                        duration=duration,
                    )

                    self.returning_wagers.append(sprite)

                case Resolution.PUSH | Resolution.NONE:
                    pass

                case _:
                    raise ValueError(
                        f"Unhandled resolution: {result.resolution}"
                    )

   
    def split_renewal_payouts(self) -> None:
        state = self.state

        for payout, net_profit, wager in self.renewal_payouts:
            vig = payout.value - net_profit

            payout.value = net_profit
            payout.render_image()

            commission = ChipSprite(
                vig,
                payout.rect.center,
                state.visible_sprites,
                radius=14,
                color=(180, 130, 45),
            )

            commission.move_to(
                state.dealer_position,
                duration=self.travel_duration(),
            )

            self.renewal_vig_chips.append(commission)

            if net_profit <= 0:
                payout.kill()
                self.payout_sprites.remove(payout)

        self.renewal_payouts.clear()


    def place(
        self,
        wager: Wager,
        destination: tuple[float, float],
    ) -> None:
        state = self.state
        player_position = state.player_sprite.rect.center

        sprite = WagerSprite(
            wager,
            player_position,
            state.visible_sprites,
        )

        state.wager_sprites[wager] = sprite

        sprite.move_to(destination, duration=self.travel_duration())
        self.placing_wagers.append(sprite)

        vig = wager.collected_vig

        if vig > 0:
            vig_chip = ChipSprite(
                vig,
                player_position,
                state.visible_sprites,
                radius=14,
                color=(180, 130, 45),
            )

            vig_chip.move_to(
                state.dealer_position,
                duration=self.travel_duration(),
            )

            self.placing_vig_chips[wager] = vig_chip

        state.player_sprite.sync_bankroll()


    def adjust(
        self,
        wager: Wager,
        amount: int,
        vig_change: int,
    ) -> None:
        state = self.state

        sprite = state.wager_sprites[wager]
        player_position = state.player_sprite.rect.center
        wager_position = sprite.rect.center

        if vig_change != 0:
            self.adjusting_vig.add(wager)

        if amount > 0:
            chip = ChipSprite(
                amount,
                player_position,
                state.visible_sprites,
            )

            chip.move_to(
                wager_position,
                duration=self.travel_duration(),
            )

            # The engine already deducted the funds.
            # Reveal the deduction immediately.
            state.player_sprite.sync_bankroll()

        else:
            chip = ChipSprite(
                -amount,
                wager_position,
                state.visible_sprites,
            )

            chip.move_to(
                player_position,
                duration=self.travel_duration(),
            )

            # Show the smaller wager immediately.
            sprite.sync_value()

            # Delay the bankroll refund until arrival.
            state.player_sprite.auto_sync = False
            self.adjustment_refund_pending = True

        self.adjustment_chips.append(chip)

        # Additional upfront commission.
        if vig_change > 0:
            vig_chip = ChipSprite(
                vig_change,
                player_position,
                state.visible_sprites,
                radius=14,
                color=(180, 130, 45),
            )

            vig_chip.move_to(
                state.dealer_position,
                duration=self.travel_duration(),
            )

            self.adjustment_chips.append(vig_chip)

        # Refunded upfront commission.
        elif vig_change < 0:
            vig_chip = ChipSprite(
                -vig_change,
                state.dealer_position,
                state.visible_sprites,
                radius=14,
                color=(180, 130, 45),
            )

            vig_chip.move_to(
                player_position,
                duration=self.travel_duration(),
            )

            self.adjustment_chips.append(vig_chip)


    def remove(
        self,
        wager: Wager,
        vig_refund: int,
    ) -> None:
        state = self.state

        sprite = state.wager_sprites[wager]
        player_position = state.player_sprite.rect.center

        # The engine has already removed the wager
        # and refunded the player's actual bankroll.
        state.player_sprite.auto_sync = False

        # Return wager principal to the player.
        sprite.move_to(
            player_position,
            duration=self.travel_duration(),
        )

        self.removing_wagers.append(sprite)

        # Return any refundable commission.
        if vig_refund > 0:
            refund = ChipSprite(
                vig_refund,
                state.dealer_position,
                state.visible_sprites,
                radius=14,
                color=(180, 130, 45),
            )

            refund.move_to(
                player_position,
                duration=self.travel_duration(),
            )

            self.refunding_vig_chips.append(refund)


    def update_removal(self) -> None:
        state = self.state

        moving = [
            *self.removing_wagers,
            *self.refunding_vig_chips,
        ]

        if not moving:
            return

        if any(sprite.is_animating for sprite in moving):
            return

        # Wager principal has reached the player.
        for sprite in self.removing_wagers:
            sprite.kill()
            state.wager_sprites.pop(sprite.wager, None)

        self.removing_wagers.clear()

        # Refunded commission has reached the player.
        for sprite in self.refunding_vig_chips:
            sprite.kill()

        self.refunding_vig_chips.clear()

        # Reveal the full refund after arrival.
        state.player_sprite.sync_bankroll()
        state.player_sprite.auto_sync = True


    def update_placement(self) -> None:
        self.placing_wagers = [
            sprite
            for sprite in self.placing_wagers
            if sprite.is_animating
        ]

        for wager, sprite in list(self.placing_vig_chips.items()):
            if not sprite.is_animating:
                sprite.kill()
                del self.placing_vig_chips[wager]

     
    def update_adjustment(self) -> None:
        state = self.state

        if not self.adjustment_chips:
            return

        if any(
            sprite.is_animating
            for sprite in self.adjustment_chips
        ):
            return

        for sprite in self.adjustment_chips:
            sprite.kill()

        self.adjustment_chips.clear()

        if self.adjustment_refund_pending:
            state.player_sprite.sync_bankroll()
            state.player_sprite.auto_sync = True
            self.adjustment_refund_pending = False

        for sprite in state.wager_sprites.values():
            if not sprite.auto_sync_value:
                sprite.sync_value()
                sprite.auto_sync_value = True

        self.adjusting_vig.clear()
   

    def update_resolution(self) -> bool:
        state = self.state

        match self.payout_stage:

            case "simultaneous":
                moving = [
                    *self.resolving_sprites,
                    *self.returning_wagers,
                    *self.moving_wagers,
                    *self.payout_sprites,
                    *self.renewal_vig_chips,
                ]

                if any(sprite.is_animating for sprite in moving):
                    return False

                for sprite in self.resolving_sprites:
                    sprite.kill()
                    state.wager_sprites.pop(sprite.wager, None)

                    if getattr(state, "test_wager", None) is sprite.wager:
                        del state.test_wager

                for sprite in self.returning_wagers:
                    sprite.kill()
                    state.wager_sprites.pop(sprite.wager, None)

                for sprite in self.payout_sprites:
                    sprite.kill()

                for sprite in self.renewal_vig_chips:
                    sprite.kill()

                self.resolving_sprites.clear()
                self.returning_wagers.clear()
                self.moving_wagers.clear()
                self.payout_sprites.clear()
                self.renewal_vig_chips.clear()
                self.renewal_payouts.clear()
                self.renewing_vig.clear()

                state.player_sprite.sync_bankroll()
                state.player_sprite.auto_sync = True
                state.sync_wager_sprites()

                self.payout_stage = "idle"
                return True


            case "arriving":
                moving = [
                    *self.resolving_sprites,
                    *self.payout_sprites,
                    *self.moving_wagers,
                ]

                if any(sprite.is_animating for sprite in moving):
                    return False

                # Remove losing wagers.
                for sprite in self.resolving_sprites:
                    sprite.kill()
                    state.wager_sprites.pop(sprite.wager, None)

                    if getattr(state, "test_wager", None) is sprite.wager:
                        del state.test_wager

                self.resolving_sprites.clear()
                self.moving_wagers.clear()

                # Split gross payouts into net payouts and vig.
                self.split_renewal_payouts()

                player_position = state.player_sprite.rect.center

                # Return winnings to the player.
                for sprite in self.payout_sprites:
                    sprite.move_to(
                        player_position,
                        duration=self.travel_duration(),
                    )

                # Return wager principal when appropriate.
                for sprite in self.returning_wagers:
                    sprite.move_to(
                        player_position,
                        duration=self.travel_duration(),
                    )

                self.payout_stage = "returning"
                return False

            case "returning":
                moving = [
                    *self.payout_sprites,
                    *self.returning_wagers,
                    *self.renewal_vig_chips,
                ]

                if any(sprite.is_animating for sprite in moving):
                    return False

                # Remove completed payout sprites.
                for sprite in self.payout_sprites:
                    sprite.kill()

                # Remove returned wager sprites.
                for sprite in self.returning_wagers:
                    sprite.kill()
                    state.wager_sprites.pop(sprite.wager, None)

                # Remove collected commission sprites.
                for sprite in self.renewal_vig_chips:
                    sprite.kill()

                self.renewal_vig_chips.clear()
                self.renewing_vig.clear()
                self.returning_wagers.clear()
                self.payout_sprites.clear()

                # Reveal the engine's final bankroll.
                state.player_sprite.sync_bankroll()
                state.player_sprite.auto_sync = True

                state.sync_wager_sprites()
                self.payout_stage = "idle"

                return True

            case "idle":
                return True

            case _:
                raise RuntimeError(
                    f"Unknown payout stage: {self.payout_stage}"
                )

    
    def reset_resolution(self) -> None:
        self.resolving_sprites.clear()
        self.returning_wagers.clear()
        self.moving_wagers.clear()
        self.payout_sprites.clear()
        self.renewal_payouts.clear()
        self.renewal_vig_chips.clear()
        self.renewing_vig.clear()
    
    
    def update(self) -> bool:
        """
        Update all wager animations.

        Returns True only when the current roll's
        wager-resolution animation finishes.
        """
        self.update_placement()
        self.update_adjustment()
        self.update_removal()

        if self.payout_stage != "idle":
            return self.update_resolution()

        return False