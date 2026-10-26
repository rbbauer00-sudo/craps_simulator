from __future__ import annotations
import pygame as pg
from .base_state import BaseState
from .roll_phase import RollPhase
from pygame.constants import *
from engine import GameRollResult, Wager, defs, Resolution, WagerType, GameRuleViolation, VigSetting
from ui.game_elements import DiceSprite, PuckSprite, WagerSprite, PlayerSprite, ChipSprite, VigSprite
from ui.animations.wager_animation_controller import WagerAnimationController

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui import CrapsApp
    from engine import Game as GameEngine

class RollBuffer:
    def __init__(self):
        self.buffer: str = ""

    def add(self, char: str) -> None:
        candidate = self.buffer + char

        if char == ",":
            # Allow comma only after a single 1-6
            if len(self.buffer) == 1 and self.buffer in "123456":
                self.buffer = candidate

        elif char in "0123456789":
            # Only allow digits 1-6 to follow a comma
            if "," in self.buffer:
                if len(self.buffer) == 2 and char in "123456":
                    self.buffer = candidate

            # If no comma, allow any digit that results in a total of 1-12
            elif (candidate in map(str, range(1, 13))):
                self.buffer = candidate


    def parse(self) -> tuple[int | None] | None:
        buffer = self.buffer
        self.clear()

        if not buffer:
            return None, None

        try:
            parts = buffer.split(",")

            if len(parts) == 1:
                total = int(parts[0])
                if 2 <= total <= 12:
                    return total, None

            elif len(parts) == 2:
                d1, d2 = map(int, parts)
                if 1 <= d1 <= 6 and 1 <= d2 <= 6:
                    return d1, d2

        except ValueError:
            pass

        return None

    def clear(self) -> None:
        self.buffer = ""
        

class PlayingState(BaseState):
    COME_BOX_POSITION = (290, 250)

    COME_POSITIONS = {
        4: (170, 190),
        5: (280, 190),
        6: (390, 190),
        8: (500, 190),
        9: (610, 190),
        10: (720, 190),
    }

    def __init__(self, app: CrapsApp):
        super().__init__(app)
        self.engine = app.engine

        self.visible_sprites = pg.sprite.Group()
        self.clickable_sprites = pg.sprite.Group()

        self.vig_sprites: dict[Wager, VigSprite] = {}
        self.wager_sprites: dict[Wager, WagerSprite] = {}


        # Game elements
        self.dice_sprite = DiceSprite(
            size= 50,
            topleft=(150,500),
            app=app,
            clickable_sprites=self.clickable_sprites,
            visible_sprites=self.visible_sprites,
        )   

        self.puck_sprite = PuckSprite(
            self.engine.point,
            self.visible_sprites,
        )

        self.player = (
            self.engine.players[0]
            if self.engine.players
            else self.engine.add_player()
        )

        self.player_sprite = PlayerSprite(
            self.player,
            (1000,40),
            self.visible_sprites,
        )

        self.forced_roll_buffer = RollBuffer()
        self.current_roll: GameRollResult | None = None
        self.roll_phase = RollPhase.READY


        self.dealer_position = (
            self.app.screen.get_width() / 2,
            -50,
        )


        self.wager_animator = WagerAnimationController(self)


    @property
    def is_animating(self) -> bool:
        return (
            self.roll_phase is not RollPhase.READY
            or self.wager_animator.is_animating
        )

    @property
    def dice_animation_complete(self) -> bool:
        return not self.dice_sprite.is_animating


    def animate_wager_placement(
        self,
        wager: Wager,
        destination: tuple[float, float],
    ) -> None:
        self.wager_animator.place(wager, destination)
    

    def start_wager_animation(self) -> None:
        self.roll_phase = RollPhase.WAGERS_RESOLVING
        self.wager_animator.start()


    def start_puck_animation(self) -> None:
        self.roll_phase = RollPhase.PUCK_MOVING

        if self.current_roll is None:
            raise RuntimeError("No current roll to resolve.")

        self.puck_sprite.on_roll(
            self.current_roll.point_before,
            self.current_roll.point_after,
        )


    @property
    def puck_animation_complete(self) -> bool:
        return not self.puck_sprite.is_animating


    def start_dice_return(self) -> None:
        self.roll_phase = RollPhase.DICE_RETURNING
        self.dice_sprite.start_return()

    
    @property
    def dice_return_complete(self) -> bool:
        return not self.dice_sprite.is_returning


    def finish_roll(self) -> None:
        self.current_roll = None
        self.roll_phase = RollPhase.READY
    
   
    def winning_vig_for(self, wager: Wager) -> int:
        if wager not in self.engine.wagers:
            return 0

        wager_type = wager.definition.wager_type

        match wager_type:
            case WagerType.LAY_BET:
                return wager.collected_vig

            case WagerType.PLACE_BET if wager.is_buy:
                return self.engine.calculate_vig(wager)

            case _:
                return 0


    def sync_vig_sprites(self) -> None:
        for wager, parent in self.wager_sprites.items():
            show_indicator = (
                wager.collected_vig > 0
                and not parent.is_animating
                and wager not in self.wager_animator.placing_vig_chips
                and wager not in self.wager_animator.renewing_vig
                and wager not in self.wager_animator.adjusting_vig
            )

            if show_indicator:
                if wager not in self.vig_sprites:
                    self.vig_sprites[wager] = VigSprite(parent)
            else:
                self.vig_sprites.pop(wager, None)

        for wager in list(self.vig_sprites):
            if wager not in self.wager_sprites:
                del self.vig_sprites[wager]

        for sprite in self.vig_sprites.values():
            sprite.update(0.0)


    def sync_wager_sprites(self) -> None:
        active_wagers = set(self.engine.wagers)

        # Remove sprites for resolved wagers.
        for wager, sprite in list(
            self.wager_sprites.items()
        ):
            if wager not in active_wagers:
                sprite.kill()
                del self.wager_sprites[wager]

        # Future: create sprites for wagers
        # introduced outside the UI.

  
    def handle_event(self, event: pg.event.Event) -> None:
        # Escape always works, even during animations.
        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            self.app.running = False
            return

        if self.is_animating:
            return

        match event.type:

            case pg.MOUSEBUTTONDOWN:
                if (
                    event.button == 1
                    and self.dice_sprite.rect.collidepoint(event.pos)
                ):
                    self.roll()
            
            case pg.KEYDOWN:
                match event.key:

                    case key if (
                        pg.K_0 <= key <= pg.K_9
                        or key == pg.K_COMMA
                    ):
                        self.forced_roll_buffer.add(event.unicode)

                    case pg.K_BACKSPACE:
                        self.forced_roll_buffer.clear()

                    case pg.K_RETURN:
                        self.roll()

                    case pg.K_p:
                        self.place_pass_line()

                    case pg.K_t:
                        if not hasattr(self, "test_wager"):
                            self.place_test_wager()

                    case pg.K_o:
                        wager = self.find_test_odds_wager()

                        if wager is not None:
                            wager.is_working = not wager.is_working
                        else:
                            print("No active odds wager to toggle.")

                    case pg.K_c:
                        try:
                            self.place_test_come_wager()
                        except GameRuleViolation:
                            print("Come bet not allowed.")

                    case pg.K_y:
                        try:
                            self.place_test_lay_wager()
                        except GameRuleViolation as exc:
                            print(f"Cannot place Lay bet: {exc}")

                    case pg.K_d:
                        try:
                            self.place_test_dp_wager()
                        except GameRuleViolation as exc:
                            print(f"Cannot place Don't Pass: {exc}")

                    case pg.K_l:
                        parent = self.find_test_odds_parent()

                        if parent is not None:
                            try:
                                self.place_test_odds_wager(parent)
                            except GameRuleViolation as exc:
                                print(f"Cannot place odds: {exc}")
                        else:
                            print("No eligible wager for odds.")

                    case pg.K_x:
                        try:
                            self.take_down_test_lay_wager()
                        except GameRuleViolation as exc:
                            print(f"Cannot remove Lay wager: {exc}")

                    case pg.K_b:
                        try:
                            self.place_test_buy_wager()
                        except GameRuleViolation as exc:
                            print(f"Cannot place Buy bet: {exc}")

                    case pg.K_UP | pg.K_DOWN:
                        wager = self.engine.get_wager(
                            self.player,
                            WagerType.PLACE_BET,
                            target=6,
                        )

                        if wager is not None:
                            amount = (
                                30
                                if event.key == pg.K_UP
                                else -30
                            )

                            if wager.value + amount > 0:
                                try:
                                    self.adjust_test_wager(wager, amount)
                                except GameRuleViolation as exc:
                                    print(f"Cannot adjust wager: {exc}")

                    case pg.K_RIGHT | pg.K_LEFT:
                        wager = self.engine.get_wager(
                            self.player,
                            WagerType.LAY_BET,
                            target=4,
                        )

                        if wager is not None:
                            amount = (
                                40
                                if event.key == pg.K_RIGHT
                                else -40
                            )

                            if wager.value + amount > 0:
                                try:
                                    self.adjust_test_wager(wager, amount)
                                except GameRuleViolation as exc:
                                    print(f"Cannot adjust Lay bet: {exc}")


    def roll(self) -> None:
        if self.is_animating:
            return
        
        parsed = self.forced_roll_buffer.parse() 
        
        if parsed is None:
            return

        self.player_sprite.sync_bankroll()
        self.player_sprite.auto_sync = False

        self.current_roll = self.engine.roll(*parsed)
        self.roll_phase = RollPhase.DICE_ROLLING
        
        self.dice_sprite.roll(self.current_roll.roll)



    def update(self, dt: float) -> None:
        self.visible_sprites.update(dt)
        self.dice_sprite.update(dt)

        wagers_complete = self.wager_animator.update()
        self.sync_vig_sprites()

        match self.roll_phase:
            case RollPhase.READY:
                pass

            case RollPhase.DICE_ROLLING:
                if self.dice_animation_complete:
                    self.start_wager_animation()

            case RollPhase.WAGERS_RESOLVING:
                if wagers_complete:
                    self.start_puck_animation()

            case RollPhase.PUCK_MOVING:
                if self.puck_animation_complete:
                    self.start_dice_return()

            case RollPhase.DICE_RETURNING:
                if self.dice_return_complete:
                    self.finish_roll()



    def draw(self, screen: pg.Surface):
        screen.fill((30, 30, 30))

        # Temporary rectangles
        pg.draw.rect(screen, (30, 90, 50), (20, 20, 940, 580))
        pg.draw.rect(screen, (55, 55, 55), (980, 20, 280, 580))
        pg.draw.rect(screen, (55, 55, 55), (20, 620, 1240, 160))

        self.visible_sprites.draw(screen)

        for sprite in self.vig_sprites.values():
            screen.blit(sprite.image, sprite.rect)



#=====================
# TEST CODE
#=====================

    def place_pass_line(self) -> None:
        if self.is_animating:
            return

        wager = Wager(
            definition=defs.PASS_LINE,
            player=self.player,
            game=self.engine,
            value=25,
        )

        self.engine.place_wager(wager)

        self.animate_wager_placement(
            wager,
            (450, 540),  
        )


    def place_test_wager(self) -> None:
        wager = Wager(
            definition=defs.PLACE_BET,
            player=self.player,
            game=self.engine,
            value=30,
            target=6,
        )

        self.engine.place_wager(wager)

        self.animate_wager_placement(
            wager,
            (390, 250),
        )


    def place_test_come_wager(self) -> None:
        wager = Wager(
            definition=defs.COME,
            player=self.player,
            game=self.engine,
            value=25,
        )

        self.engine.place_wager(wager)

        self.animate_wager_placement(
            wager,
            (290, 250),
        )


    def place_test_dp_wager(self) -> None:
        wager = Wager(
            definition=defs.DONT_PASS,
            player=self.player,
            game=self.engine,
            value=25,
        )

        self.engine.place_wager(wager)

        self.animate_wager_placement(
            wager,
            (600, 540),
        )


    def place_test_lay_wager(self) -> None:
        wager = Wager(
            definition=defs.LAY_BET,
            player=self.player,
            game=self.engine,
            value=40,
            target=4,
        )

        self.engine.place_wager(wager)

        self.animate_wager_placement(
            wager,
            (170, 300),
        )

        
    def place_test_odds_wager(
        self,
        parent: Wager,
        value: int = 25,
    ) -> None:

        parent_type = parent.definition.wager_type

        if parent_type in {
            WagerType.PASS_LINE,
            WagerType.COME,
        }:
            definition = defs.LINE_ODDS

        elif parent_type in {
            WagerType.DONT_PASS,
            WagerType.DONT_COME,
        }:
            definition = defs.LAY_ODDS

        else:
            raise ValueError(
                "Odds require a line, Come, or Don't Come parent."
            )

        wager = Wager(
            definition=definition,
            player=self.player,
            game=self.engine,
            value=value,
            parent_wager=parent,
        )

        self.engine.place_wager(wager)

        parent_sprite = self.wager_sprites[parent]

        x, y = parent_sprite.rect.center

        self.animate_wager_placement(
            wager,
            (x, y + 55),
        )

    
    def find_test_odds_parent(self) -> Wager | None:
        eligible_types = {
            WagerType.PASS_LINE,
            WagerType.DONT_PASS,
            WagerType.COME,
            WagerType.DONT_COME,
        }

        for wager in reversed(self.engine.wagers):
            if (
                wager.player is self.player
                and wager.definition.wager_type in eligible_types
            ):
                target = (
                    self.engine.point
                    if wager.definition.wager_type in {
                        WagerType.PASS_LINE,
                        WagerType.DONT_PASS,
                    }
                    else wager.target
                )

                if target is None:
                    continue

                has_odds = any(
                    existing.parent_wager is wager
                    for existing in self.engine.wagers
                )

                if not has_odds:
                    return wager

        return None


    def find_test_odds_wager(self) -> Wager | None:
        odds_types = {
            WagerType.LINE_ODDS,
            WagerType.LAY_ODDS,
        }

        for wager in reversed(self.engine.wagers):
            if (
                wager.player is self.player
                and wager.definition.wager_type in odds_types
            ):
                return wager

        return None


    
    def take_down_test_lay_wager(self) -> None:
        wager = self.engine.get_wager(
            self.player,
            WagerType.LAY_BET,
            target=4,
        )

        if wager is None:
            print("No Lay wager to remove.")
            return

        # Preserve the refundable commission amount.
        vig_refund = wager.collected_vig

        # Engine handles rules and accounting.
        self.engine.take_down_wager(wager)

        # Controller handles the visual return.
        self.wager_animator.remove(
            wager,
            vig_refund,
        )



    def place_test_buy_wager(self) -> None:
        wager = Wager(
            definition=defs.PLACE_BET,
            player=self.player,
            game=self.engine,
            value=20,
            target=4,
        )

        wager.is_buy = True

        self.engine.place_wager(wager)

        self.animate_wager_placement(
            wager,
            (170, 250),
        )
    

    def adjust_test_wager(
        self,
        wager: Wager,
        amount: int,
    ) -> None:
        if amount == 0:
            return

        sprite = self.wager_sprites[wager]
        old_vig = wager.collected_vig

        # Freeze the displayed wager value before
        # applying the engine adjustment.
        sprite.auto_sync_value = False

        try:
            if amount > 0:
                self.engine.increase_wager(wager, amount)
            else:
                self.engine.decrease_wager(wager, -amount)

        except Exception:
            sprite.auto_sync_value = True
            raise

        vig_change = wager.collected_vig - old_vig

        self.wager_animator.adjust(
            wager,
            amount,
            vig_change,
        )


