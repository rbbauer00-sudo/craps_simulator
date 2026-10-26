
from __future__ import annotations

from typing import TYPE_CHECKING

from engine import Resolution
from ui.game_elements import ChipSprite

if TYPE_CHECKING:
    from ui.states.playing_state import PlayingState


class WagerAnimationController:
    def __init__(self, state: PlayingState) -> None:
        self.state = state

    def start(self) -> None:
        state = self.state

        if state.current_roll is None:
            raise RuntimeError("No current roll to resolve.")

        state.resolving_sprites.clear()
        state.payout_sprites.clear()
        state.returning_wagers.clear()
        state.moving_wagers.clear()
        state.renewal_payouts.clear()
        state.renewal_vig_chips.clear()
        state.renewing_vig.clear()

        active_wagers = set(state.engine.wagers)
        state.payout_stage = "arriving"

        for result in state.current_roll.wager_results:
            sprite = state.wager_sprites.get(result.wager)

            if sprite is None:
                continue

            match result.resolution:
                case Resolution.LOSE:
                    sprite.move_to(
                        state.dealer_position,
                        duration=0.4,
                    )
                    state.resolving_sprites.append(sprite)

                case Resolution.WIN:
                    wager = result.wager

                    if wager not in active_wagers:
                        state.returning_wagers.append(sprite)

                    vig = state.winning_vig_for(wager)
                    gross_profit = result.profit + vig

                    if vig > 0:
                        state.renewing_vig.add(wager)

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
                        duration=0.4,
                        hold=0.35,
                    )

                    state.payout_sprites.append(payout)

                    if vig > 0:
                        state.renewal_payouts.append(
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
                        duration=0.4,
                    )
                    state.moving_wagers.append(sprite)

                case Resolution.REMOVE:
                    state.returning_wagers.append(sprite)

                case Resolution.PUSH | Resolution.NONE:
                    pass

                case _:
                    raise ValueError(
                        f"Unhandled resolution: {result.resolution}"
                    )

    
    def split_renewal_payouts(self) -> None:
        state = self.state

        for payout, net_profit, wager in state.renewal_payouts:
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
                duration=0.4,
            )

            state.renewal_vig_chips.append(commission)

            if net_profit <= 0:
                payout.kill()
                state.payout_sprites.remove(payout)

        state.renewal_payouts.clear()
    

    def update(self) -> bool:
        state = self.state

        match state.payout_stage:

            case "arriving":
                moving = [
                    *state.resolving_sprites,
                    *state.payout_sprites,
                    *state.moving_wagers,
                ]

                if any(sprite.is_animating for sprite in moving):
                    return False

                # Remove losing wagers.
                for sprite in state.resolving_sprites:
                    sprite.kill()
                    state.wager_sprites.pop(sprite.wager, None)

                    if getattr(state, "test_wager", None) is sprite.wager:
                        del state.test_wager

                state.resolving_sprites.clear()
                state.moving_wagers.clear()

                # Split gross payouts into net payouts and vig.
                self.split_renewal_payouts()

                player_position = state.player_sprite.rect.center

                # Return winnings to the player.
                for sprite in state.payout_sprites:
                    sprite.move_to(
                        player_position,
                        duration=0.4,
                    )

                # Return wager principal when appropriate.
                for sprite in state.returning_wagers:
                    sprite.move_to(
                        player_position,
                        duration=0.4,
                    )

                state.payout_stage = "returning"
                return False

            case "returning":
                moving = [
                    *state.payout_sprites,
                    *state.returning_wagers,
                    *state.renewal_vig_chips,
                ]

                if any(sprite.is_animating for sprite in moving):
                    return False

                # Remove completed payout sprites.
                for sprite in state.payout_sprites:
                    sprite.kill()

                # Remove returned wager sprites.
                for sprite in state.returning_wagers:
                    sprite.kill()
                    state.wager_sprites.pop(sprite.wager, None)

                # Remove collected commission sprites.
                for sprite in state.renewal_vig_chips:
                    sprite.kill()

                state.renewal_vig_chips.clear()
                state.renewing_vig.clear()
                state.returning_wagers.clear()
                state.payout_sprites.clear()

                # Reveal the engine's final bankroll.
                state.player_sprite.sync_bankroll()
                state.player_sprite.auto_sync = True

                state.sync_wager_sprites()
                state.payout_stage = "idle"

                return True

            case "idle":
                return True

            case _:
                raise RuntimeError(
                    f"Unknown payout stage: {state.payout_stage}"
                )

